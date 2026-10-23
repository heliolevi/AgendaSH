import os

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")


def get_conn():
    """Dependência do FastAPI: uma conexão por requisição (commit no sucesso, rollback no erro)."""
    with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
        yield conn
