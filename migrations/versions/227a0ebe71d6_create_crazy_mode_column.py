"""create crazy_mode column to differentiate between whether there are multiple gifters and you can send msg between gifters

Revision ID: 227a0ebe71d6
Revises: 9e95911d3dce
Create Date: 2025-10-25 16:37:05.075168

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '227a0ebe71d6'
down_revision: Union[str, Sequence[str], None] = '9e95911d3dce'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Step 1: add the column as nullable with a server default so new inserts get False.
    op.add_column(
        'secret_santa_contexts',
        sa.Column('crazy_mode', sa.Boolean(), nullable=True, server_default=sa.false()),
    )

    # Step 2: ensure any existing rows have a non-NULL value (defensive).
    # Use a bound TextClause so the execute call receives a single argument.
    op.execute(
        sa.text("UPDATE secret_santa_contexts SET crazy_mode = :val WHERE crazy_mode IS NULL").bindparams(val=False)
    )
    op.alter_column('secret_santa_contexts',
                    'crazy_mode',
                    nullable=False,
                    server_default=None
                    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('secret_santa_contexts', 'crazy_mode')
