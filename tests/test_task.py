import pytest
from sqlalchemy import delete

from kernel.db.models.task import Task, TaskStatus
from kernel.db.session import AsyncSessionLocal


async def clear_tasks() -> None:
    async with AsyncSessionLocal() as session:
        await session.execute(delete(Task))
        await session.commit()


@pytest.mark.asyncio
async def test_task_creation():
    await clear_tasks()

    async with AsyncSessionLocal() as session:
        task = Task(
            title="Research vector DBs",
        )

        session.add(task)
        await session.commit()
        await session.refresh(task)

        assert task.id is not None
        assert task.status == TaskStatus.PENDING
        assert task.attempt_count == 0
        assert task.max_retries == 0
        assert task.created_at is not None
        assert task.updated_at is not None
