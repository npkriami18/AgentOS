from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from kernel.db.models.task import Task


class Scheduler:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self.session_factory = session_factory

    async def next_task(self) -> Task | None:
        async with self.session_factory() as session:
            result = await session.execute(
                select(Task)
                .where(Task.status == "PENDING")
                .order_by(Task.id.asc())
                .limit(1)
            )
            return result.scalar_one_or_none()

    async def mark_running(self, task_id: str) -> Task | None:
        return await self._set_status(task_id, "RUNNING")

    async def mark_completed(self, task_id: str) -> Task | None:
        return await self._set_status(task_id, "COMPLETED")

    async def mark_failed(self, task_id: str) -> Task | None:
        return await self._set_status(task_id, "FAILED")

    async def _set_status(self, task_id: str, status: str) -> Task | None:
        async with self.session_factory() as session:
            task = await session.get(Task, task_id)
            if task is None:
                return None

            task.status = status
            await session.commit()
            await session.refresh(task)
            return task
