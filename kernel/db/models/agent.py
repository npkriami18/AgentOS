from uuid import uuid4

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from kernel.db.base import Base


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="idle", nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    tool_names: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
