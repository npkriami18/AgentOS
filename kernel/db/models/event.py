from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import JSON, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from kernel.db.base import Base


class Event(Base):
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    type: Mapped[str] = mapped_column(
        String,
        nullable=False,
        index=True,
    )

    payload: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    correlation_id: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
        index=True,
    )
