from uuid import uuid4

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from kernel.db.base import Base


class Event(Base):
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid4())
    )

    type: Mapped[str] = mapped_column(String, nullable=False)

    payload: Mapped[str] = mapped_column(String, nullable=False)
