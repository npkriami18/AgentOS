from datetime import datetime, timezone

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from kernel.db.models.task import Task, TaskStatus


class Scheduler:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self.session_factory = session_factory

    async def next_task(self) -> Task | None:
        async with self.session_factory() as session:
            result = await session.execute(
                select(Task)
                .where(
                    or_(
                        Task.status == TaskStatus.PENDING,
                        Task.status == TaskStatus.RETRYING,
                    )
                )
                .order_by(Task.created_at.asc(), Task.id.asc())
                .limit(1)
            )
            return result.scalar_one_or_none()

    async def mark_running(self, task_id: str) -> Task | None:
        return await self._set_status(
            task_id,
            TaskStatus.RUNNING,
            started_at=datetime.now(timezone.utc),
            attempt_count=Task.attempt_count + 1,
            last_error=None,
        )

    async def mark_completed(self, task_id: str) -> Task | None:
        return await self._set_status(
            task_id,
            TaskStatus.COMPLETED,
            completed_at=datetime.now(timezone.utc),
        )

    async def mark_failed(self, task_id: str, error: str | None = None) -> Task | None:
        return await self._set_status(task_id, TaskStatus.FAILED, last_error=error)

    async def mark_paused(self, task_id: str) -> Task | None:
        return await self._set_status(task_id, TaskStatus.PAUSED)

    async def mark_retrying(
        self,
        task_id: str,
        error: str | None = None,
    ) -> Task | None:
        return await self._set_status(task_id, TaskStatus.RETRYING, last_error=error)

    async def _set_status(
        self,
        task_id: str,
        status: TaskStatus,
        **updates: object,
    ) -> Task | None:
        async with self.session_factory() as session:
            task = await session.get(Task, task_id)
            if task is None:
                return None

            task.status = str(status)
            for field, value in updates.items():
                setattr(task, field, value)
            task.updated_at = datetime.now(timezone.utc)
            await session.commit()
            await session.refresh(task)
            return task
