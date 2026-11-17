"""Cria a tabela verificacao_email (códigos enviados por e-mail). Idempotente.
Rodar uma vez por banco:  cd backend && python -m app.modules.verificacao.criar_tabela
"""
import psycopg

from app.core.database import DATABASE_URL

SQL = """
CREATE TABLE IF NOT EXISTS verificacao_email (
    id_verificacao SERIAL PRIMARY KEY,
    email          VARCHAR(100) NOT NULL,
    finalidade     VARCHAR(20)  NOT NULL CHECK (finalidade IN ('cadastro', 'senha')),
    codigo_hash    VARCHAR(64)  NOT NULL,
    expira_em      TIMESTAMPTZ  NOT NULL,
    tentativas     INT          NOT NULL DEFAULT 0,
    usado          BOOLEAN      NOT NULL DEFAULT FALSE,
    criado_em      TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_verificacao_email_busca ON verificacao_email (email, finalidade, criado_em DESC);
"""

if __name__ == "__main__":
    with psycopg.connect(DATABASE_URL, connect_timeout=90) as conn:
        conn.execute(SQL)
    print("Tabela verificacao_email pronta.")
