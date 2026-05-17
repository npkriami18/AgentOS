"""add agent metadata and tools

Revision ID: <new_revision>
Revises: 1b2c3d4e5f6g
Create Date: 2026-05-17 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "<new_revision>"
down_revision: Union[str, Sequence[str], None] = "1b2c3d4e5f6g"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("agents", sa.Column("description", sa.String(), nullable=True))
    op.add_column("agents", sa.Column("metadata_json", sa.JSON(), nullable=True))
    op.add_column("agents", sa.Column("tool_names", sa.JSON(), nullable=True))

    op.execute(
        "UPDATE agents SET metadata_json = '{}'::json WHERE metadata_json IS NULL"
    )
    op.execute("UPDATE agents SET tool_names = '[]'::json WHERE tool_names IS NULL")

    op.alter_column("agents", "metadata_json", nullable=False)
    op.alter_column("agents", "tool_names", nullable=False)


def downgrade() -> None:
    op.drop_column("agents", "tool_names")
    op.drop_column("agents", "metadata_json")
    op.drop_column("agents", "description")
