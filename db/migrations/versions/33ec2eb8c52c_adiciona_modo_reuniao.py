"""adiciona_modo_reuniao

Revision ID: 33ec2eb8c52c
Revises: d8ebcb6c110d
Create Date: 2026-11-16 17:03:08.614070

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '33ec2eb8c52c'
down_revision: Union[str, Sequence[str], None] = 'd8ebcb6c110d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE reuniao
        ADD COLUMN IF NOT EXISTS modo VARCHAR(20) NOT NULL DEFAULT 'presencial';
    """)

    op.execute("""
        UPDATE reuniao
        SET modo = 'online'
        WHERE ID_sala IS NULL;
    """)

    op.execute("""
        ALTER TABLE reuniao
        ADD CONSTRAINT chk_reuniao_modo 
        CHECK (modo IN ('presencial', 'online'));
    """)

    op.execute("""
        ALTER TABLE reuniao
        ADD CONSTRAINT chk_reuniao_sala_por_modo
        CHECK (
            (modo = 'online' AND ID_sala IS NULL) OR
            (modo = 'presencial' AND ID_sala IS NOT NULL)
        );
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE reuniao DROP CONSTRAINT IF EXISTS chk_reuniao_sala_por_modo;")
    op.execute("ALTER TABLE reuniao DROP CONSTRAINT IF EXISTS chk_reuniao_modo;")
    op.execute("ALTER TABLE reuniao DROP COLUMN IF EXISTS modo;")
