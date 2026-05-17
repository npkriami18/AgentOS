import pytest
from sqlalchemy import delete

from kernel.db.models.task import Task
from kernel.db.session import AsyncSessionLocal
from kernel.events.bus import EventBus
from kernel.runtime.engine import RuntimeEngine
from kernel.runtime.scheduler import Scheduler


async def clear_tasks() -> None:
    async with AsyncSessionLocal() as session:
        await session.execute(delete(Task))
        await session.commit()


async def create_task(title: str) -> Task:
    async with AsyncSessionLocal() as session:
        task = Task(title=title)
        session.add(task)
        await session.commit()
        await session.refresh(task)
        return task


async def fetch_task(task_id: str) -> Task | None:
    async with AsyncSessionLocal() as session:
        return await session.get(Task, task_id)


@pytest.mark.asyncio
async def test_runtime_executes_pending_task():
    await clear_tasks()
    task = await create_task("Run task")

    executed = []

    async def executor(task_obj: Task) -> None:
        executed.append(task_obj.id)

    engine = RuntimeEngine(
        scheduler=Scheduler(AsyncSessionLocal),
        event_bus=EventBus(AsyncSessionLocal),
        executor=executor,
    )

    worked = await engine.run_once()
    refreshed = await fetch_task(task.id)

    assert worked is True
    assert executed == [task.id]
    assert refreshed is not None
    assert refreshed.status == "COMPLETED"


@pytest.mark.asyncio
async def test_runtime_marks_failed_task():
    await clear_tasks()
    task = await create_task("Fail task")

    async def executor(task_obj: Task) -> None:
        raise RuntimeError("boom")

    engine = RuntimeEngine(
        scheduler=Scheduler(AsyncSessionLocal),
        event_bus=EventBus(AsyncSessionLocal),
        executor=executor,
    )

    with pytest.raises(RuntimeError, match="boom"):
        await engine.run_once()

    refreshed = await fetch_task(task.id)

    assert refreshed is not None
    assert refreshed.status == "FAILED"
