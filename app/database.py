import duckdb
from datetime import datetime, date, timedelta
from pathlib import Path
from contextlib import contextmanager
from typing import Optional, Dict, Any, List

DB_PATH = Path("data/assistant.duckdb")


@contextmanager
def get_connection():
    """Conexão com o DuckDB"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB_PATH))
    try:
        yield con
    finally:
        con.close()


def init_database():
    with get_connection() as con:
        # Tabela Transitions | transioções, registros financeiros
        con.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id BIGINT PRIMARY KEY,
                type VARCHAR(10) NOT NULL,           -- 'income' ou 'expense'
                description VARCHAR NOT NULL,
                amount DECIMAL(10,2) NOT NULL,
                category VARCHAR(50),
                date DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # tabela user_settings | tabela sobre o usuário
        con.execute("""
            CREATE TABLE IF NOT EXISTS user_settings (
                key VARCHAR(50) PRIMARY KEY,
                value VARCHAR(255),
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # tabela calendario
        con.execute("""
            CREATE TABLE IF NOT EXISTS calendar (
                date DATE PRIMARY KEY,
                year INTEGER,
                month INTEGER,
                month_name VARCHAR(20),
                day INTEGER,
                day_of_week INTEGER,
                day_name VARCHAR(20),
                week_of_year INTEGER,
                is_weekend BOOLEAN,
                quarter INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Ppreencher calendário
        count = con.execute("SELECT COUNT(*) FROM calendar").fetchone()[0]
        if count == 0:
            con.execute("""
                INSERT INTO calendar (date, year, month, month_name, day, day_of_week, day_name, week_of_year, is_weekend, quarter)
                SELECT 
                    date::DATE,
                    EXTRACT(year FROM date),
                    EXTRACT(month FROM date),
                    strftime(date, '%B'),
                    EXTRACT(day FROM date),
                    EXTRACT(dow FROM date),
                    strftime(date, '%A'),
                    EXTRACT(week FROM date),
                    (EXTRACT(dow FROM date) IN (0, 6)),
                    EXTRACT(quarter FROM date)
                FROM generate_series(DATE '2025-01-01', DATE '2030-12-31', INTERVAL '1 day') AS t(date)
            """)

        # Views, calculos pré feitos
        
        # View: Saldo atual
        con.execute("""
            CREATE OR REPLACE VIEW v_balance AS
            SELECT 
                COALESCE(SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END), 0) AS total_income,
                COALESCE(SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END), 0) AS total_expense,
                COALESCE(SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END), 0) - 
                COALESCE(SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END), 0) AS current_balance
            FROM transactions
        """)

        # View: Totais por categoria
        con.execute("""
            CREATE OR REPLACE VIEW v_category_totals AS
            SELECT 
                category,
                type,
                COUNT(*) AS transaction_count,
                SUM(amount) AS total_amount
            FROM transactions
            WHERE category IS NOT NULL
            GROUP BY category, type
            ORDER BY total_amount DESC
        """)

        # View: Resumo mensal
        con.execute("""
            CREATE OR REPLACE VIEW v_monthly_summary AS
            SELECT 
                strftime('%Y-%m', date) AS month,
                SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) AS income,
                SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) AS expense,
                SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) - 
                SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) AS net
            FROM transactions
            GROUP BY month
            ORDER BY month DESC
        """)


# Config usuário

def save_user_setting(key: str, value: str) -> None:
    """Salva ou atualiza uma configuração do usuário."""
    with get_connection() as con:
        con.execute("""
            INSERT OR REPLACE INTO user_settings (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        """, [key, value])


def get_user_setting(key: str) -> Optional[str]:
    """Busca uma configuração do usuário."""
    with get_connection() as con:
        result = con.execute(
            "SELECT value FROM user_settings WHERE key = ?", 
            [key]
        ).fetchone()
        return result[0] if result else None


# Config transações

def get_today() -> str:
    """Retorna a data de hoje no formato YYYY-MM-DD."""
    return datetime.now().date().isoformat()


def insert_transaction(
    description: str,
    amount: float,
    type_: str,                    
    category: Optional[str] = None,
    date: Optional[str] = None
) -> int:
    """
    Insere uma transação financeira (entrada ou saída).
    - Se 'date' não for informada, usa a data de hoje.
    - Aceita formatos: YYYY-MM-DD, DD/MM/YYYY, ou palavras ('hoje', 'ontem', 'amanhã').
    """
    today = datetime.now().date()
    parsed_date = today

    if date:
        date_str = str(date).strip().lower()

        # Tenta formato ISO primeiro (mais confiável)
        try:
            parsed_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            pass

        # Tenta outros formatos comuns
        if parsed_date == today:
            for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
                try:
                    parsed_date = datetime.strptime(date_str, fmt).date()
                    break
                except ValueError:
                    continue

        # Palavras relativas
        if parsed_date == today:
            if date_str in ("hoje", "today", "agora"):
                parsed_date = today
            elif date_str in ("ontem", "yesterday"):
                parsed_date = today - timedelta(days=1)
            elif date_str in ("amanhã", "amanha", "tomorrow"):
                parsed_date = today + timedelta(days=1)
            else:
                # Se não conseguiu interpretar, usa hoje + avisa no futuro
                parsed_date = today

    final_date = parsed_date.strftime("%Y-%m-%d")
    new_id = int(datetime.now().timestamp() * 1000)

    with get_connection() as con:
        con.execute("""
            INSERT INTO transactions (id, type, description, amount, category, date, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, [new_id, type_, description, amount, category, final_date, datetime.now()])

    return new_id


def get_transactions(
    limit: int = 10,
    type_: Optional[str] = None,
    category: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Busca transações com filtros opcionais."""
    with get_connection() as con:
        query = """
            SELECT id, type, description, amount, category, date, created_at 
            FROM transactions 
            WHERE 1=1
        """
        params = []

        if type_:
            query += " AND type = ?"
            params.append(type_)

        if category:
            query += " AND category = ?"
            params.append(category)

        query += " ORDER BY date DESC, created_at DESC LIMIT ?"
        params.append(limit)

        result = con.execute(query, params).fetchall()

    return [
        {
            "id": row[0],
            "type": row[1],
            "description": row[2],
            "amount": float(row[3]),
            "category": row[4],
            "date": str(row[5]),
            "created_at": str(row[6])
        }
        for row in result
    ]


def get_balance() -> Dict[str, float]:
    """Retorna o saldo atual usando a View v_balance."""
    with get_connection() as con:
        result = con.execute("SELECT * FROM v_balance").fetchone()

    return {
        "total_income": float(result[0]),
        "total_expense": float(result[1]),
        "balance": float(result[2])
    }


# Inicialização

if __name__ != "__main__":
    init_database()
