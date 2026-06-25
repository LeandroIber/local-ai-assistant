"""
Módulo responsável pela conexão e operações com o banco de dados DuckDB.
"""

import duckdb
from datetime import datetime, timedelta
from pathlib import Path
from contextlib import contextmanager
from typing import Optional, Dict, Any, List


DB_PATH = Path("data/assistant.duckdb")


@contextmanager
def get_connection():
    """Context manager para conexão segura com o banco de dados."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB_PATH))
    try:
        yield con
    finally:
        con.close()


def init_database():
    """Inicializa o banco de dados com as tabelas necessárias."""
    with get_connection() as con:
        
        # TABELA PRINCIPAL
        con.execute("""
            CREATE TABLE IF NOT EXISTS principal (
                id BIGINT PRIMARY KEY,
                type VARCHAR(50) NOT NULL,
                data JSON NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                source VARCHAR(50) DEFAULT 'chat'
            )
        """)

        # Tabela específica de gastos
        con.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id BIGINT PRIMARY KEY,
                description VARCHAR NOT NULL,
                amount DECIMAL(10,2) NOT NULL,
                category VARCHAR,
                date DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


# Função antiga de inserção
def insert_record(record_type: str, data: Dict[str, Any], source: str = "chat") -> int:
    """
    Insere um registro genérico na tabela 'principal'.
    Retorna o ID do registro inserido.
    """
    new_id = int(datetime.now().timestamp() * 1000)

    with get_connection() as con:
        con.execute("""
            INSERT INTO principal (id, type, data, created_at, source)
            VALUES (?, ?, ?, ?, ?)
        """, [new_id, record_type, data, datetime.now(), source])
    
    return new_id


# Função específica para inserir gastos (melhorada com parsing de data)
def insert_expense(
    description: str, 
    amount: float, 
    category: Optional[str] = None, 
    date: Optional[str] = None
) -> int:
    """
    Insere um gasto na tabela específica 'expenses'.
    Aceita date em formato YYYY-MM-DD ou tenta interpretar valores comuns
    como 'hoje', 'ontem', 'amanhã'. Se falhar, usa data atual.
    Retorna o ID do registro inserido.
    """
    parsed_date = None
    if date:
        date_str = str(date).strip().lower()
        today = datetime.now().date()

        # Tenta formato padrão YYYY-MM-DD
        try:
            parsed_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            pass

        # Tenta formatos alternativos comuns
        if not parsed_date:
            for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
                try:
                    parsed_date = datetime.strptime(date_str, fmt).date()
                    break
                except ValueError:
                    continue

        # Palavras-chave relativas
        if not parsed_date:
            if date_str in ("hoje", "today", "agora"):
                parsed_date = today
            elif date_str in ("ontem", "yesterday"):
                parsed_date = today - timedelta(days=1)
            elif date_str in ("amanhã", "amanha", "tomorrow"):
                parsed_date = today + timedelta(days=1)
            elif "segunda" in date_str or "monday" in date_str:
                days_ahead = 0 - today.weekday()
                if days_ahead <= 0:
                    days_ahead += 7
                parsed_date = today + timedelta(days=days_ahead)

        if not parsed_date:
            parsed_date = today
    else:
        parsed_date = datetime.now().date()

    final_date_str = parsed_date.strftime("%Y-%m-%d")

    new_id = int(datetime.now().timestamp() * 1000)

    with get_connection() as con:
        con.execute("""
            INSERT INTO expenses (id, description, amount, category, date, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, [new_id, description, amount, category, final_date_str, datetime.now()])
    
    return new_id


# Função para consultar/listar gastos
def get_expenses(limit: int = 10, category: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Busca os gastos mais recentes da tabela 'expenses'.
    Pode filtrar por categoria.
    Retorna uma lista de dicionários.
    """
    with get_connection() as con:
        if category:
            query = """
                SELECT id, description, amount, category, date, created_at 
                FROM expenses 
                WHERE category = ?
                ORDER BY date DESC, created_at DESC 
                LIMIT ?
            """
            result = con.execute(query, [category, limit]).fetchall()
        else:
            query = """
                SELECT id, description, amount, category, date, created_at 
                FROM expenses 
                ORDER BY date DESC, created_at DESC 
                LIMIT ?
            """
            result = con.execute(query, [limit]).fetchall()

    # Converte o resultado em lista de dicionários
    expenses_list = []
    for row in result:
        expenses_list.append({
            "id": row[0],
            "description": row[1],
            "amount": float(row[2]),
            "category": row[3],
            "date": str(row[4]),
            "created_at": str(row[5])
        })
    
    return expenses_list
