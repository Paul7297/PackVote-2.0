"""Add trip destination suggestions.

Revision ID: b14d6ce9a472
Revises: 55d81fb5d1b5
Create Date: 2026-10-07
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "b14d6ce9a472"
down_revision: Union[str, Sequence[str], None] = "55d81fb5d1b5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "trip_destination_suggestions",
        sa.Column("trip_id", sa.UUID(), nullable=False),
        sa.Column("suggested_by", sa.UUID(), nullable=False),
        sa.Column("external_place_id", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("country", sa.String(length=100), nullable=True),
        sa.Column("region", sa.String(length=100), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("trip_destination_id", sa.UUID(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["trip_id"], ["trips.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["suggested_by"], ["users.id"]),
        sa.ForeignKeyConstraint(
            ["trip_destination_id"],
            ["trip_destinations.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "trip_id",
            "external_place_id",
            name="uq_trip_destination_suggestion_place",
        ),
    )
    op.create_index(
        "ix_trip_destination_suggestions_trip_id",
        "trip_destination_suggestions",
        ["trip_id"],
    )
    op.create_index(
        "ix_trip_destination_suggestions_suggested_by",
        "trip_destination_suggestions",
        ["suggested_by"],
    )
    op.create_index(
        "ix_trip_destination_suggestions_trip_destination_id",
        "trip_destination_suggestions",
        ["trip_destination_id"],
    )
    op.create_index(
        "ix_trip_destination_suggestions_status",
        "trip_destination_suggestions",
        ["status"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_trip_destination_suggestions_status",
        table_name="trip_destination_suggestions",
    )
    op.drop_index(
        "ix_trip_destination_suggestions_trip_destination_id",
        table_name="trip_destination_suggestions",
    )
    op.drop_index(
        "ix_trip_destination_suggestions_suggested_by",
        table_name="trip_destination_suggestions",
    )
    op.drop_index(
        "ix_trip_destination_suggestions_trip_id",
        table_name="trip_destination_suggestions",
    )
    op.drop_table("trip_destination_suggestions")
