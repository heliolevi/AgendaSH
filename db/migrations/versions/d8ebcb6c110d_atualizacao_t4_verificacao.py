"""atualizacao_t4_verificacao

Revision ID: d8ebcb6c110d
Revises: f061184be2a4
Create Date: 2026-11-05 17:20:45.218993

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd8ebcb6c110d'
down_revision: Union[str, Sequence[str], None] = 'f061184be2a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE usuario
        ADD COLUMN IF NOT EXISTS verificado BOOLEAN DEFAULT FALSE,
        ADD COLUMN IF NOT EXISTS tipo_conta VARCHAR(200) DEFAULT 'comum';
    """)

    op.execute('UPDATE usuario SET verificado = FALSE')

    op.execute("""
        CREATE TABLE IF NOT EXISTS codigo_verificacao(
            ID_codigo INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            ID_usuario INT NOT NULL REFERENCES usuario(ID_usuario) ON DELETE CASCADE,
            codigo VARCHAR(6) NOT NULL,
            usado BOOLEAN DEFAULT FALSE,
            expira_em TIMESTAMP NOT NULL,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)


def downgrade() -> None:
    op.execute("DROP TABLE EXISTS codigo_verificacao,")

    op.execute("""
        ALTER TABLE usuario
        DROP COLUMN IF EXISTS verificado,
        DROP COLUMN IF EXISTS tipo_conta;
    """)

