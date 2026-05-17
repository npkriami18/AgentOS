from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from kernel.db.models.event import Event

EventHandler = Callable[[Event], Awaitable[None]]


class EventBus:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self.session_factory = session_factory
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        self._handlers[event_type].append(handler)

    async def publish(
        self,
        event_type: str,
        payload: dict[str, Any],
        correlation_id: str | None = None,
    ) -> Event:
        async with self.session_factory() as session:
            event = Event(
                type=event_type,
                payload=payload,
                correlation_id=correlation_id,
            )
            session.add(event)
            await session.commit()
            await session.refresh(event)

        for handler in self._handlers.get(event_type, []):
            await handler(event)

        return event

    async def replay(
        self,
        event_type: str | None = None,
        correlation_id: str | None = None,
    ) -> list[Event]:
        async with self.session_factory() as session:
            stmt = select(Event).order_by(Event.timestamp.asc(), Event.id.asc())

            if event_type is not None:
                stmt = stmt.where(Event.type == event_type)

            if correlation_id is not None:
                stmt = stmt.where(Event.correlation_id == correlation_id)

            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def replay_to_handlers(
        self,
        event_type: str | None = None,
        correlation_id: str | None = None,
    ) -> list[Event]:
        events = await self.replay(
            event_type=event_type,
            correlation_id=correlation_id,
        )

        for event in events:
            for handler in self._handlers.get(event.type, []):
                await handler(event)

        return events
