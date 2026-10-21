"""criar_tabelas_iniciais

Revision ID: c2f5c4180c4d
Revises: 
Create Date: 2026-10-20 17:34:43.573095

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c2f5c4180c4d'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
    CREATE TABLE IF NOT EXISTS usuario(
        ID_usuario INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        nome VARCHAR(100) NOT NULL,
        email VARCHAR(100) NOT NULL UNIQUE,
        senha_hash VARCHAR(200) NOT NULL,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    op.execute("""
    CREATE TABLE IF NOT EXISTS sala(
        ID_sala INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        nome VARCHAR(100) NOT NULL,
        capacidade INT NOT NULL,
        tipo VARCHAR(250) NOT NULL,
        localizacao_link TEXT
    );
    """)
    
    op.execute("""
    CREATE TABLE IF NOT EXISTS reuniao(
        ID_reuniao INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        ID_usuario INT REFERENCES usuario(ID_usuario),
        ID_sala INT REFERENCES sala(ID_sala),
        titulo VARCHAR(200) NOT NULL,
        descricao TEXT,
        data_inicio TIMESTAMP NOT NULL,
        data_fim TIMESTAMP NOT NULL,
        comeca_em TIMESTAMP DEFAULT CURRENT_DATE
    );
    """)
    
    op.execute("""
    CREATE TABLE IF NOT EXISTS convite(
        ID_reuniao INT REFERENCES reuniao(ID_reuniao),
        ID_usuario INT REFERENCES usuario(ID_usuario),
        status_resposta VARCHAR(100),
        data_hora TIMESTAMP,
        PRIMARY KEY (ID_reuniao, ID_usuario)
    );
    """)

def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS convite;")
    op.execute("DROP TABLE IF EXISTS reuniao;")
    op.execute("DROP TABLE IF EXISTS sala;")
    op.execute("DROP TABLE IF EXISTS usuario;")
