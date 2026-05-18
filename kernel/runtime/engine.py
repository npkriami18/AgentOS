import asyncio
from collections.abc import Awaitable, Callable

from kernel.db.models.task import Task
from kernel.events.bus import EventBus
from kernel.events.types import TASK_COMPLETED, TASK_FAILED, TASK_STARTED
from kernel.runtime.scheduler import Scheduler

TaskExecutor = Callable[[Task], Awaitable[None]]


class RuntimeEngine:
    def __init__(
        self,
        scheduler: Scheduler,
        event_bus: EventBus,
        executor: TaskExecutor,
    ) -> None:
        self.scheduler = scheduler
        self.event_bus = event_bus
        self.executor = executor
        self._running = False

    async def run_once(self) -> bool:
        task = await self.scheduler.next_task()
        if task is None:
            return False

        task = await self.scheduler.mark_running(task.id)
        if task is None:
            return False
        await self.event_bus.publish(TASK_STARTED, {"task_id": task.id})

        try:
            await self._execute_task(task)
        except Exception as exc:
            error_message = str(exc)
            if task.attempt_count <= task.max_retries:
                await self.scheduler.mark_retrying(task.id, error=error_message)
            else:
                await self.scheduler.mark_failed(task.id, error=error_message)
            await self.event_bus.publish(
                TASK_FAILED,
                {"task_id": task.id, "error": error_message},
            )
            raise

        await self.scheduler.mark_completed(task.id)
        await self.event_bus.publish(TASK_COMPLETED, {"task_id": task.id})
        return True

    async def _execute_task(self, task: Task) -> None:
        if task.timeout_seconds is None:
            await self.executor(task)
            return

        try:
            await asyncio.wait_for(
                self.executor(task),
                timeout=task.timeout_seconds,
            )
        except TimeoutError as exc:
            message = f"Task timed out after {task.timeout_seconds} seconds"
            raise TimeoutError(message) from exc

    async def run_loop(self, poll_interval: float = 1.0) -> None:
        self._running = True
        while self._running:
            worked = await self.run_once()
            if not worked:
                await asyncio.sleep(poll_interval)

    def stop(self) -> None:
        self._running = False
