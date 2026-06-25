"""
Módulo de ferramentas (tools) para o Local AI Assistant.
"""

from typing import Optional
from app.database import init_database, insert_expense, get_expenses


def save_expense(
    description: str,
    amount: float,
    category: Optional[str] = None,
    date: Optional[str] = None
) -> str:
    """
    Salva um gasto no banco de dados.
    IMPORTANTE: Esta ferramenta só deve ser chamada DEPOIS que o usuário confirmar explicitamente
    com palavras como 'sim', 'confirma', 'pode registrar', etc.
    """
    try:
        insert_expense(
            description=description,
            amount=amount,
            category=category,
            date=date
        )

        category_text = f" na categoria '{category}'" if category else ""
        return f"Gasto de R$ {amount:.2f} ({description}){category_text} salvo com sucesso!"

    except Exception as e:
        return f"Erro ao salvar o gasto: {str(e)}"


def list_expenses(limit: int = 5, category: Optional[str] = None) -> str:
    """
    Lista os gastos mais recentes, com opção de filtrar por categoria.
    """
    try:
        expenses = get_expenses(limit=limit, category=category)

        if not expenses:
            if category:
                return f"Nenhum gasto encontrado na categoria '{category}'."
            return "Você ainda não possui gastos registrados."

        if category:
            response = f"Gastos na categoria '{category}' (últimos {len(expenses)}):\n\n"
        else:
            response = f"Seus {len(expenses)} gastos mais recentes:\n\n"

        for exp in expenses:
            cat = f" ({exp['category']})" if exp.get('category') else ""
            response += f"• {exp['date']} - R$ {exp['amount']:.2f} - {exp['description']}{cat}\n"

        return response.strip()

    except Exception as e:
        return f"Erro ao buscar os gastos: {str(e)}"


def initialize_system():
    """Inicializa o banco de dados."""
    init_database()


# ============================================================
# TOOL SCHEMAS
# ============================================================

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "save_expense",
            "description": "Salva um novo gasto no sistema. USE SOMENTE depois que o usuário confirmar explicitamente com palavras como 'sim', 'confirma', 'pode registrar', 'ok' ou similar. Nunca chame direto sem confirmação prévia do usuário. Parâmetros: descrição clara, valor numérico, categoria opcional e data no formato YYYY-MM-DD.",
            "parameters": {
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "Descrição clara do gasto. Exemplo: 'café da manhã', 'uber', 'aluguel'"
                    },
                    "amount": {
                        "type": "number",
                        "description": "Valor do gasto em reais (número). Exemplo: 25.5"
                    },
                    "category": {
                        "type": "string",
                        "description": "Categoria do gasto (opcional). Exemplos: transporte, alimentação, moradia, lazer"
                    },
                    "date": {
                        "type": "string",
                        "description": "Data no formato YYYY-MM-DD (opcional). Se não informado, usa a data atual."
                    }
                },
                "required": ["description", "amount"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_expenses",
            "description": "Lista gastos registrados. Use quando o usuário pedir para ver, mostrar ou consultar seus gastos. Chame imediatamente, sem pedir confirmação.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Quantidade de gastos para retornar. Padrão é 5."
                    },
                    "category": {
                        "type": "string",
                        "description": "Filtrar por categoria (opcional). Exemplo: transporte, alimentação"
                    }
                },
                "required": []
            }
        }
    }
]
