
"""Add archive timestamp to trips.

Revision ID: d8f3a2c91b47
Revises: 252460a7d91d
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d8f3a2c91b47"
down_revision: Union[str, Sequence[str], None] = "b14d6ce9a472"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "trips",
        sa.Column(
            "archived_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("trips", "archived_at")
