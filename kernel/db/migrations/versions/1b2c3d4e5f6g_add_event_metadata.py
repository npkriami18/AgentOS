"""add event metadata

Revision ID: 1b2c3d4e5f6g
Revises: a53eb75a18b6
Create Date: 2026-05-17 13:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "1b2c3d4e5f6g"
down_revision: Union[str, Sequence[str], None] = "a53eb75a18b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "events",
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "events",
        sa.Column("correlation_id", sa.String(), nullable=True),
    )
    op.add_column(
        "events",
        sa.Column("payload_json", sa.JSON(), nullable=True),
    )

    op.execute("UPDATE events SET timestamp = NOW() WHERE timestamp IS NULL")

    # Wrap old string payload inside JSON so no cast failure occurs.
    op.execute("""
        UPDATE events
        SET payload_json = json_build_object('raw', payload)
        WHERE payload_json IS NULL
        """)

    op.drop_column("events", "payload")
    op.alter_column("events", "payload_json", new_column_name="payload")

    op.create_index(op.f("ix_events_type"), "events", ["type"], unique=False)
    op.create_index(op.f("ix_events_timestamp"), "events", ["timestamp"], unique=False)
    op.create_index(
        op.f("ix_events_correlation_id"),
        "events",
        ["correlation_id"],
        unique=False,
    )

    op.alter_column("events", "timestamp", nullable=False)
    op.alter_column("events", "payload", nullable=False)
