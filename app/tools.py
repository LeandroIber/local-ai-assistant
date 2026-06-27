"""
tools.py - Ferramentas do Assistente Financeiro Local
"""

from typing import Optional, List, Dict, Any
from app.database import (
    init_database,
    insert_transaction,
    get_transactions,
    get_balance as db_get_balance,
    get_connection
)


def initialize_system():
    """Inicializa o banco de dados."""
    init_database()


# FERRAMENTAS DE ESCRITA

def save_transaction(
    description: str,
    amount: float,
    type_: str,
    category: Optional[str] = None,
    date: Optional[str] = None
) -> str:
    """
    Registra uma transação financeira (entrada ou saída de dinheiro).
    Use SOMENTE depois que o usuário confirmar explicitamente que deseja salvar.
    """
    try:
        if type_ not in ["income", "expense"]:
            return "Erro: O tipo deve ser 'income' (entrada) ou 'expense' (saída)."

        insert_transaction(
            description=description,
            amount=amount,
            type_=type_,
            category=category,
            date=date
        )

        tipo_texto = "Entrada" if type_ == "income" else "Saída"
        cat_text = f" na categoria '{category}'" if category else ""
        date_text = f" em {date}" if date else ""

        return (
            f"{tipo_texto} de R$ {amount:.2f} registrada com sucesso!\n"
            f"Descrição: {description}{cat_text}{date_text}"
        )

    except Exception as e:
        return f"Erro ao registrar a transação: {str(e)}"


# FERRAMENTAS DE CONSULTA

def list_transactions(
    limit: int = 10,
    type_: Optional[str] = None,
    category: Optional[str] = None
) -> str:
    """Lista as transações registradas. Pode filtrar por tipo (income/expense) e categoria."""
    try:
        transactions = get_transactions(limit=limit, type_=type_, category=category)

        if not transactions:
            if type_:
                return f"Nenhuma transação do tipo '{type_}' foi encontrada."
            return "Você ainda não possui transações registradas."

        tipo_filtro = f" do tipo '{type_}'" if type_ else ""
        cat_filtro = f" na categoria '{category}'" if category else ""

        response = f"Últimas {len(transactions)} transações{tipo_filtro}{cat_filtro}:\n\n"

        for t in transactions:
            tipo = "Entrada" if t["type"] == "income" else "Saída"
            cat = f" ({t['category']})" if t.get("category") else ""
            response += f"- {t['date']} | {tipo} R$ {t['amount']:.2f} - {t['description']}{cat}\n"

        return response.strip()

    except Exception as e:
        return f"Erro ao buscar transações: {str(e)}"


def get_balance() -> str:
    """Retorna o saldo atual do usuário (Total de Entradas - Total de Saídas)."""
    try:
        balance = db_get_balance()
        return (
            "Resumo Financeiro Atual:\n"
            f"- Total de Entradas: R$ {balance['total_income']:.2f}\n"
            f"- Total de Saídas:   R$ {balance['total_expense']:.2f}\n"
            f"- Saldo Atual:       R$ {balance['balance']:.2f}"
        )
    except Exception as e:
        return f"Erro ao calcular o saldo: {str(e)}"


def get_monthly_summary() -> str:
    """Retorna um resumo financeiro agrupado por mês (receitas, despesas e saldo líquido)."""
    try:
        with get_connection() as con:
            result = con.execute("""
                SELECT month, income, expense, net 
                FROM v_monthly_summary 
                ORDER BY month DESC 
                LIMIT 6
            """).fetchall()

        if not result:
            return "Ainda não há transações suficientes para gerar um resumo mensal."

        response = "Resumo Financeiro por Mês:\n\n"
        for row in result:
            month, income, expense, net = row
            response += (
                f"Mês: {month}\n"
                f"  Entradas: R$ {float(income):.2f}\n"
                f"  Saídas:   R$ {float(expense):.2f}\n"
                f"  Saldo:    R$ {float(net):.2f}\n\n"
            )
        return response.strip()

    except Exception as e:
        return f"Erro ao gerar resumo mensal: {str(e)}"


def get_category_summary() -> str:
    """Mostra o total gasto/recebido por categoria."""
    try:
        with get_connection() as con:
            result = con.execute("""
                SELECT category, type, total_amount 
                FROM v_category_totals 
                ORDER BY total_amount DESC 
                LIMIT 15
            """).fetchall()

        if not result:
            return "Ainda não há transações categorizadas."

        response = "Resumo por Categoria:\n\n"

        # Separa income e expense para melhor visualização
        expenses = [r for r in result if r[1] == "expense"]
        incomes = [r for r in result if r[1] == "income"]

        if expenses:
            response += "Saídas por Categoria:\n"
            for cat, _, amount in expenses:
                response += f"- {cat or 'Sem categoria'}: R$ {float(amount):.2f}\n"
            response += "\n"

        if incomes:
            response += "Entradas por Categoria:\n"
            for cat, _, amount in incomes:
                response += f"- {cat or 'Sem categoria'}: R$ {float(amount):.2f}\n"

        return response.strip()

    except Exception as e:
        return f"Erro ao gerar resumo por categoria: {str(e)}"


# LISTA DE FERRAMENTAS (para o LLM)

TOOLS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "save_transaction",
            "description": (
                "Registra uma transação financeira (entrada de dinheiro ou saída/gasto). "
                "Use esta ferramenta APENAS depois que o usuário confirmar explicitamente que quer salvar a transação. "
                "Nunca chame esta ferramenta sem confirmação prévia."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "Descrição clara da transação (ex: 'Salário', 'Aluguel', 'Supermercado')"
                    },
                    "amount": {
                        "type": "number",
                        "description": "Valor da transação em reais (use ponto como separador decimal)"
                    },
                    "type_": {
                        "type": "string",
                        "description": "Tipo da transação: 'income' para entrada/receita ou 'expense' para saída/gasto",
                        "enum": ["income", "expense"]
                    },
                    "category": {
                        "type": "string",
                        "description": "Categoria da transação (ex: 'Salário', 'Moradia', 'Alimentação', 'Transporte'). Opcional."
                    },
                    "date": {
                        "type": "string",
                        "description": (
                            "Data da transação no formato YYYY-MM-DD. "
                            "Se não for informada, usa a data de hoje automaticamente. "
                            "Exemplos válidos: '2026-06-26', 'hoje', 'ontem', '2026-06-20'"
                        )
                    }
                },
                "required": ["description", "amount", "type_"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_transactions",
            "description": "Lista as transações registradas. Pode filtrar por tipo (income/expense) e categoria.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Quantidade máxima de transações a retornar (padrão: 10)"
                    },
                    "type_": {
                        "type": "string",
                        "description": "Filtrar por tipo: 'income' ou 'expense'"
                    },
                    "category": {
                        "type": "string",
                        "description": "Filtrar por categoria específica"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_balance",
            "description": "Retorna o saldo atual do usuário: total de entradas, total de saídas e saldo líquido.",
            "parameters": {"type": "object", "properties": {}},
            "required": []
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_monthly_summary",
            "description": (
                "Retorna um resumo financeiro agrupado por mês, mostrando entradas, saídas e saldo líquido de cada mês. "
                "Útil para ver a evolução financeira ao longo do tempo."
            ),
            "parameters": {"type": "object", "properties": {}},
            "required": []
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_category_summary",
            "description": (
                "Mostra o total de entradas e saídas agrupado por categoria. "
                "Excelente para entender onde o dinheiro está sendo gasto ou recebido."
            ),
            "parameters": {"type": "object", "properties": {}},
            "required": []
        }
    }
]
