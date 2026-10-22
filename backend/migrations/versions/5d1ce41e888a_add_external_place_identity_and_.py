"""add external place identity and optional destination enrichment

Revision ID: 5d1ce41e888a
Revises: dee6c1bbd4e1
Create Date: 2026-10-05 23:08:45.316554

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "5d1ce41e888a"
down_revision: Union[str, Sequence[str], None] = "dee6c1bbd4e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "destinations",
        sa.Column(
            "external_place_id",
            sa.String(length=255),
            nullable=True,
        ),
    )

    op.add_column(
        "destinations",
        sa.Column(
            "provider_name",
            sa.String(length=50),
            nullable=True,
        ),
    )

    op.alter_column(
        "destinations",
        "climate",
        existing_type=sa.VARCHAR(length=20),
        nullable=True,
    )

    op.alter_column(
        "destinations",
        "cost_tier",
        existing_type=sa.VARCHAR(length=20),
        nullable=True,
    )

    op.alter_column(
        "destinations",
        "suitable_travel_styles",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        nullable=True,
    )

    op.alter_column(
        "destinations",
        "suitable_activities",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        nullable=True,
    )

    op.alter_column(
        "destinations",
        "suitable_traveler_types",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        nullable=True,
    )

    op.create_unique_constraint(
        "uq_destination_provider_place",
        "destinations",
        ["provider_name", "external_place_id"],
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_constraint(
        "uq_destination_provider_place",
        "destinations",
        type_="unique",
    )

    op.alter_column(
        "destinations",
        "suitable_traveler_types",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        nullable=False,
    )

    op.alter_column(
        "destinations",
        "suitable_activities",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        nullable=False,
    )

    op.alter_column(
        "destinations",
        "suitable_travel_styles",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        nullable=False,
    )

    op.alter_column(
        "destinations",
        "cost_tier",
        existing_type=sa.VARCHAR(length=20),
        nullable=False,
    )

    op.alter_column(
        "destinations",
        "climate",
        existing_type=sa.VARCHAR(length=20),
        nullable=False,
    )

    op.drop_column(
        "destinations",
        "provider_name",
    )

    op.drop_column(
        "destinations",
        "external_place_id",
    )
    # ### end Alembic commands ###
