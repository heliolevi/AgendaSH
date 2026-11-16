"""Cria a tabela reuniao_fixa e a coluna reuniao.id_fixa (só adiciona, não altera dados). Idempotente.
Rodar uma vez por banco:  cd backend && python -m app.modules.reunioes_fixas.criar_tabela
"""
import psycopg

from app.core.database import DATABASE_URL

SQL = """
CREATE TABLE IF NOT EXISTS reuniao_fixa (
    id_fixa     SERIAL PRIMARY KEY,
    id_usuario  INT REFERENCES usuario(id_usuario),
    id_sala     INT REFERENCES sala(id_sala),
    titulo      VARCHAR(200) NOT NULL,
    descricao   TEXT,
    dia_semana  SMALLINT NOT NULL CHECK (dia_semana BETWEEN 0 AND 6),  -- 0 = segunda ... 6 = domingo
    hora_inicio TIME NOT NULL,
    hora_fim    TIME NOT NULL CHECK (hora_fim > hora_inicio),
    data_inicio DATE NOT NULL,          -- primeira data em que a série pode valer
    data_fim    DATE,                   -- NULL = sem data para acabar
    criado_em   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
ALTER TABLE reuniao ADD COLUMN IF NOT EXISTS id_fixa INT REFERENCES reuniao_fixa(id_fixa) ON DELETE SET NULL;
"""

if __name__ == "__main__":
    with psycopg.connect(DATABASE_URL, connect_timeout=90) as conn:
        conn.execute(SQL)
    print("Tabela reuniao_fixa e coluna reuniao.id_fixa prontas.")
