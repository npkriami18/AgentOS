"""add task lifecycle fields

Revision ID: 2d7d9c9f0c40
Revises: 1b2c3d4e5f6g
Create Date: 2026-05-17 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2d7d9c9f0c40"
down_revision: Union[str, Sequence[str], None] = "1b2c3d4e5f6g"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "tasks",
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "tasks",
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "tasks",
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "tasks",
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "tasks",
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "tasks",
        sa.Column("max_retries", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "tasks",
        sa.Column("timeout_seconds", sa.Integer(), nullable=True),
    )
    op.add_column(
        "tasks",
        sa.Column("last_error", sa.String(), nullable=True),
    )
    op.create_index(op.f("ix_tasks_created_at"), "tasks", ["created_at"], unique=False)

    op.execute(
        "UPDATE tasks SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL"
    )
    op.execute(
        "UPDATE tasks SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL"
    )

    op.alter_column("tasks", "created_at", nullable=False)
    op.alter_column("tasks", "updated_at", nullable=False)
    op.alter_column("tasks", "attempt_count", server_default=None)
    op.alter_column("tasks", "max_retries", server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_tasks_created_at"), table_name="tasks")
    op.drop_column("tasks", "last_error")
    op.drop_column("tasks", "timeout_seconds")
    op.drop_column("tasks", "max_retries")
    op.drop_column("tasks", "attempt_count")
    op.drop_column("tasks", "completed_at")
    op.drop_column("tasks", "started_at")
    op.drop_column("tasks", "updated_at")
    op.drop_column("tasks", "created_at")
