"""adiciona_restricao

Revision ID: f061184be2a4
Revises: c2f5c4180c4d
Create Date: 2026-10-22 16:33:36.086253

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f061184be2a4'
down_revision: Union[str, Sequence[str], None] = 'c2f5c4180c4d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist;")

    op.execute("""
    ALTER TABLE reuniao 
        ADD CONSTRAINT restricoes_sala_horario 
        EXCLUDE USING gist (
        ID_sala WITH =,
        tsrange(data_inicio, data_fim) WITH &&
    );
    """)

    op.execute("""
    ALTER TABLE eventos 
        ADD CONSTRAINT restricoes_eventos_horario 
        EXCLUDE USING gist (
        ID_sala WITH =,
        tsrange(data_inicio, data_fim) WITH &&
    );
    """)

def downgrade() -> None:
    op.execute("ALTER TABLE reuniao DROP CONSTRAINT IF EXISTS restricoes_sala_horario;")
    op.execute("ALTER TABLE eventos DROP CONSTRAINT IF EXISTS restricoes_eventos_horario;")

