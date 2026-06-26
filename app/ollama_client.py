"""
Módulo responsável pela comunicação com o Ollama e Function Calling.
"""

import ollama
from typing import List, Dict, Any, Optional
from app.tools import save_expense, list_expenses, initialize_system, TOOLS
from app.prompt import SYSTEM_PROMPT


# Nome do modelo
MODEL_NAME = "qwen3:8b"



# ESTADO DE CONFIRMAÇÃO PENDENTE (por sessão)
pending_expenses: List[Dict[str, Any]] = []


def get_available_tools() -> List[Dict[str, Any]]:
    return TOOLS


def _is_confirmation_message(text: str) -> bool:
    """Verifica se a mensagem do usuário é uma confirmação afirmativa."""
    if not text:
        return False
    text_lower = text.lower().strip()
    confirmation_keywords = [
        "sim", "confirma", "confirmo", "pode registrar", "pode", "ok", "yes",
        "confirmar", "registra", "salva", "salvar", "registra aí", "pode sim",
        "afirmativo", "beleza", "fechado", "vai", "manda"
    ]
    return any(kw in text_lower for kw in confirmation_keywords)


def _is_cancel_message(text: str) -> bool:
    """Verifica se a mensagem é para cancelar gastos pendentes."""
    if not text:
        return False
    text_lower = text.lower().strip()
    cancel_keywords = ["não", "nao", "cancelar", "cancela", "esquece", "não confirma", "cancel"]
    return any(kw in text_lower for kw in cancel_keywords)


def chat_with_tools(messages: List[Dict[str, str]]) -> str:
    """
    Envia mensagens para o Ollama e processa Function Calling quando necessário.
    Implementa fluxo de confirmação para save_expense.
    """
    global pending_expenses

    try:
        initialize_system()

        # Extrai última mensagem do usuário (para checar confirmação/cancelamento)
        last_user_message = ""
        if messages and isinstance(messages[-1], dict) and messages[-1].get("role") == "user":
            last_user_message = messages[-1].get("content", "") or ""

        # 1. Se há gastos pendentes, verifica se usuário confirmou ou cancelou
        if pending_expenses:
            if _is_confirmation_message(last_user_message):
                # Executa todos os gastos pendentes
                results = []
                for pend in pending_expenses:
                    result = save_expense(
                        description=pend.get("description", ""),
                        amount=float(pend.get("amount", 0)),
                        category=pend.get("category"),
                        date=pend.get("date")
                    )
                    results.append(result)

                count = len(pending_expenses)
                pending_expenses.clear()

                if count == 1:
                    return results[0]
                else:
                    header = f"✅ {count} gastos registrados com sucesso:\n"
                    return header + "\n".join(f"• {r}" for r in results)

            elif _is_cancel_message(last_user_message):
                count = len(pending_expenses)
                pending_expenses.clear()
                return f"❌ Ok, cancelei. Nenhum dos {count} gasto(s) foi registrado."

            else:
                # Ainda há pendentes mas usuário não confirmou nem cancelou
                # Relembra a confirmação (não chama LLM ainda)
                summaries = []
                for p in pending_expenses:
                    cat = f" ({p['category']})" if p.get("category") else ""
                    summaries.append(f"• {p['description']} - R$ {float(p['amount']):.2f}{cat}")
                summary_text = "\n".join(summaries)
                return (
                    f"Ainda tenho estes gastos pendentes de confirmação:\n{summary_text}\n\n"
                    "Responda com 'sim', 'confirma' ou 'pode registrar' para salvar, ou 'não' para cancelar."
                )

        # 2. Fluxo normal: adiciona system prompt e chama o modelo
        full_messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ] + messages

        response = ollama.chat(
            model=MODEL_NAME,
            messages=full_messages,
            tools=get_available_tools(),
            think=False
        )

        # Se o modelo decidiu usar alguma ferramenta
        if response.message.tool_calls:
            # Verificamos se há chamada para save_expense (precisa de confirmação)
            save_calls = []
            list_results = []

            for tool_call in response.message.tool_calls:
                function_name = tool_call.function.name
                arguments = tool_call.function.arguments or {}

                if function_name == "save_expense":
                    # NÃO executamos ainda! Guardamos como pendente.
                    pend = {
                        "description": arguments.get("description", ""),
                        "amount": arguments.get("amount", 0),
                        "category": arguments.get("category"),
                        "date": arguments.get("date")
                    }
                    pending_expenses.append(pend)
                    save_calls.append(pend)

                elif function_name == "list_expenses":
                    # list_expenses é imediato, executamos agora
                    result = list_expenses(
                        limit=arguments.get("limit", 5),
                        category=arguments.get("category")
                    )
                    list_results.append(result)

            # Se houve chamada de save_expense → pedimos confirmação (sem salvar ainda)
            if save_calls:
                summaries = []
                for p in save_calls:
                    cat_text = f" na categoria '{p['category']}'" if p.get("category") else ""
                    date_text = f" ({p['date']})" if p.get("date") else ""
                    summaries.append(f"• {p['description']} - R$ {float(p['amount']):.2f}{cat_text}{date_text}")

                summary_text = "\n".join(summaries)
                plural = "s" if len(save_calls) > 1 else ""
                return (
                    f"Identifiquei o{plural} seguinte{plural} gasto{plural}:\n{summary_text}\n\n"
                    "Confirma que posso registrar? Responda 'sim', 'confirma' ou 'pode registrar'."
                )

            # Se só houve list_expenses (sem save), retornamos o resultado diretamente
            if list_results:
                return list_results[0] if len(list_results) == 1 else "\n\n".join(list_results)

            # Caso raro de outras tools
            return "Operação processada."

        # Se não usou ferramenta, retorna a resposta normal do modelo
        return response.message.content or "Desculpe, não entendi sua solicitação."

    except Exception as e:
        # Limpa pendentes em caso de erro grave para evitar loop
        if pending_expenses:
            pending_expenses.clear()
        return f"Erro ao comunicar com o Ollama: {str(e)}"
