import pytest
from sqlalchemy import delete, select

from kernel.db.models.event import Event
from kernel.db.session import AsyncSessionLocal
from kernel.events.bus import EventBus
from kernel.events.types import TASK_COMPLETED, TASK_CREATED


async def clear_events() -> None:
    async with AsyncSessionLocal() as session:
        await session.execute(delete(Event))
        await session.commit()


@pytest.mark.asyncio
async def test_event_publishing():
    await clear_events()

    bus = EventBus(AsyncSessionLocal)
    received: list[Event] = []

    async def handler(event: Event) -> None:
        received.append(event)

    bus.subscribe(TASK_CREATED, handler)

    event = await bus.publish(
        TASK_CREATED,
        {"task_id": "123", "title": "Research vector DBs"},
        correlation_id="corr-1",
    )

    assert event.id is not None
    assert event.timestamp is not None
    assert event.correlation_id == "corr-1"
    assert len(received) == 1
    assert received[0].type == TASK_CREATED


@pytest.mark.asyncio
async def test_event_persistence():
    await clear_events()

    bus = EventBus(AsyncSessionLocal)

    created = await bus.publish(
        TASK_COMPLETED,
        {"task_id": "t-1", "result": "done"},
        correlation_id="corr-2",
    )

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Event).where(Event.id == created.id))
        saved_event = result.scalar_one()

    assert saved_event.type == TASK_COMPLETED
    assert saved_event.payload["result"] == "done"


@pytest.mark.asyncio
async def test_event_replay():
    await clear_events()

    bus = EventBus(AsyncSessionLocal)

    await bus.publish(TASK_CREATED, {"task_id": "1"}, correlation_id="workflow-1")
    await bus.publish(TASK_COMPLETED, {"task_id": "1"}, correlation_id="workflow-1")
    await bus.publish(TASK_CREATED, {"task_id": "2"}, correlation_id="workflow-2")

    events = await bus.replay(correlation_id="workflow-1")

    assert len(events) == 2
    assert events[0].type == TASK_CREATED
    assert events[1].type == TASK_COMPLETED
