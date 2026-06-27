"""
ollama_client.py - Gerencia a comunicação com o Ollama e execução de ferramentas
"""

import ollama
from typing import List, Dict, Any
from app.tools import (
    save_transaction,
    list_transactions,
    get_balance,
    get_monthly_summary,
    get_category_summary,
    initialize_system,
    TOOLS
)
from app.database import get_user_setting, save_user_setting
from app.prompt import SYSTEM_PROMPT


MODEL_NAME = "qwen3:8b"


# Estado
pending_transactions: List[Dict[str, Any]] = []
user_name: str = None
awaiting_name: bool = False


def get_available_tools() -> List[Dict[str, Any]]:
    return TOOLS


def _safe_text(text: str) -> str:
    """Versão mais robusta para evitar erro de encoding/surrogates."""
    if not text:
        return ""
    try:
        # Remove caracteres surrogates e inválidos de forma agressiva
        text = text.encode("utf-8", errors="ignore").decode("utf-8", errors="ignore")
        # Remove caracteres problemáticos remanescentes
        text = text.replace("\udc00", "").replace("\udc01", "").replace("\udc02", "")
        return text.strip()
    except Exception:
        return ""


def _is_confirmation_message(text: str) -> bool:
    if not text:
        return False
    text_lower = text.lower().strip()
    keywords = ["sim", "confirma", "pode registrar", "ok", "pode", "yes", "registra", "salva"]
    return any(kw in text_lower for kw in keywords)


def _is_cancel_message(text: str) -> bool:
    if not text:
        return False
    text_lower = text.lower().strip()
    keywords = ["nao", "cancelar", "cancela", "esquece"]
    return any(kw in text_lower for kw in keywords)


def _extract_name(raw_text: str) -> str:
    """Extrai o nome do usuário de forma inteligente."""
    text = raw_text.strip().lower()

    prefixes = [
        "me chame de", "pode me chamar de", "meu nome é",
        "é só me chamar de", "me chama de", "chama de",
        "pode chamar de", "me chame só de"
    ]

    for prefix in prefixes:
        if text.startswith(prefix):
            text = text.replace(prefix, "", 1).strip()
            break

    text = text.strip(" '\".,!?").title()
    return text


def chat_with_tools(messages: List[Dict[str, str]]) -> str:
    global pending_transactions, user_name, awaiting_name

    try:
        initialize_system()

        if user_name is None:
            user_name = get_user_setting("user_name")

        last_user_message = ""
        if messages and messages[-1].get("role") == "user":
            last_user_message = messages[-1].get("content", "") or ""

        # FLUXO DE CONFIRMAÇÃO DE TRANSAÇÕES
        if pending_transactions:
            if _is_confirmation_message(last_user_message):
                results = []
                for pend in pending_transactions:
                    result = save_transaction(
                        description=pend.get("description", ""),
                        amount=float(pend.get("amount", 0)),
                        type_=pend.get("type_", "expense"),
                        category=pend.get("category"),
                        date=pend.get("date")
                    )
                    results.append(result)

                count = len(pending_transactions)
                pending_transactions.clear()
                return "\n".join(results) if count == 1 else f"{count} transações registradas com sucesso."

            elif _is_cancel_message(last_user_message):
                count = len(pending_transactions)
                pending_transactions.clear()
                return f"Cancelei. Nenhuma das {count} transações foi registrada."

            else:
                summaries = []
                for p in pending_transactions:
                    tipo = "Entrada" if p.get("type_") == "income" else "Gasto"
                    summaries.append(f"- {tipo}: {p['description']} - R$ {float(p['amount']):.2f}")
                return "Transações pendentes:\n" + "\n".join(summaries) + "\n\nConfirma que posso registrar?"

        # FLUXO DE BOAS-VINDAS / NOME DO USUÁRIO
        if not user_name:
            if not awaiting_name:
                awaiting_name = True
                return (
                    "Olá! Eu sou o Alfred, seu assistente financeiro pessoal.\n\n"
                    "Para eu te atender melhor, como posso te chamar?"
                )
            else:
                name = _extract_name(last_user_message)
                if len(name) < 2:
                    return "Por favor, me diga um nome válido."
                save_user_setting("user_name", name)
                user_name = name
                awaiting_name = False
                return f"Prazer em te conhecer, **{user_name}**! Como posso te ajudar hoje?"

        # FLUXO NORMAL
        personalized_prompt = SYSTEM_PROMPT
        if user_name:
            personalized_prompt = (
                f"Você está conversando com {user_name}. "
                f"Use o nome dele nas respostas quando fizer sentido.\n\n" + SYSTEM_PROMPT
            )

        full_messages = [{"role": "system", "content": personalized_prompt}] + messages

        response = ollama.chat(
            model=MODEL_NAME,
            messages=full_messages,
            tools=get_available_tools(),
            think=False
        )

        if response.message.tool_calls:
            for tool_call in response.message.tool_calls:
                name = tool_call.function.name
                args = tool_call.function.arguments or {}

                if name == "save_transaction":
                    pend = {
                        "description": args.get("description", ""),
                        "amount": args.get("amount", 0),
                        "type_": args.get("type_", "expense"),
                        "category": args.get("category"),
                        "date": args.get("date")
                    }
                    pending_transactions.append(pend)

                elif name == "list_transactions":
                    return list_transactions(
                        limit=args.get("limit", 10),
                        type_=args.get("type_"),
                        category=args.get("category")
                    )

                elif name == "get_balance":
                    return get_balance()

                elif name == "get_monthly_summary":
                    return get_monthly_summary()

                elif name == "get_category_summary":
                    return get_category_summary()

            if pending_transactions:
                summaries = []
                for p in pending_transactions:
                    tipo = "Entrada" if p.get("type_") == "income" else "Gasto"
                    summaries.append(f"- {tipo}: {p['description']} - R$ {float(p['amount']):.2f}")
                return "Identifiquei as seguintes transações:\n" + "\n".join(summaries) + "\n\nConfirma que posso registrar?"

            return "Operação processada."

        return _safe_text(response.message.content) or "Não entendi."

    except Exception as e:
        if pending_transactions:
            pending_transactions.clear()
        # Retorna mensagem de erro limpa
        error_msg = str(e)
        return f"Erro: {error_msg[:200]}" if len(error_msg) > 200 else f"Erro: {error_msg}"
