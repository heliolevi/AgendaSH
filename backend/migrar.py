"""Migracao: adiciona a coluna 'papel' na tabela usuario e (opcional) promove um admin.

Uso (dentro de backend/, com o venv ativo e o .env preenchido):
    python migrar.py                      # so cria a coluna (idempotente)
    python migrar.py 002-02xxxx@aluno.undb.edu.br   # cria a coluna e torna esse e-mail admin
"""
import os
import sys

import psycopg
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

ADICIONAR_COLUNA = (
    "ALTER TABLE usuario "
    "ADD COLUMN IF NOT EXISTS papel VARCHAR(20) NOT NULL DEFAULT 'membro'"
)

if not DATABASE_URL:
    print("DATABASE_URL nao definido no .env"); sys.exit(1)

with psycopg.connect(DATABASE_URL) as conn:
    conn.execute(ADICIONAR_COLUNA)
    print("OK: coluna 'papel' garantida (default 'membro').")
    if len(sys.argv) > 1:
        email = sys.argv[1].strip().lower()
        n = conn.execute(
            "UPDATE usuario SET papel = 'admin' WHERE lower(email) = %s", (email,)
        ).rowcount
        print(f"OK: {n} usuario(s) promovido(s) a admin ({email})." if n
              else f"Nenhum usuario com o e-mail {email}.")
    conn.commit()
