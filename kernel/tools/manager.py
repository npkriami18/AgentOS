import asyncio
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from kernel.agents.registry import AgentRegistry
from kernel.events.bus import EventBus
from kernel.events.types import TOOL_CALLED
from kernel.tools.base import BaseTool, ToolContext
from kernel.tools.errors import (
    ToolNotFoundError,
    ToolPermissionError,
    ToolRateLimitError,
)


@dataclass(slots=True)
class ToolLogEntry:
    agent_id: str
    tool_name: str
    arguments: dict[str, Any]
    success: bool
    started_at: datetime
    completed_at: datetime
    error: str | None = None


@dataclass(slots=True)
class RateLimit:
    calls: int
    per_seconds: int


class ToolManager:
    def __init__(
        self,
        agent_registry: AgentRegistry,
        event_bus: EventBus,
        default_timeout_seconds: float = 5.0,
        default_rate_limit: RateLimit | None = None,
    ) -> None:
        self.agent_registry = agent_registry
        self.event_bus = event_bus
        self.default_timeout_seconds = default_timeout_seconds
        self.default_rate_limit = default_rate_limit
        self._tools: dict[str, BaseTool] = {}
        self._rate_limits: dict[str, RateLimit] = {}
        self._call_history: dict[tuple[str, str], deque[datetime]] = {}
        self._logs: list[ToolLogEntry] = []

    def register_tool(
        self,
        tool: BaseTool,
        rate_limit: RateLimit | None = None,
    ) -> None:
        self._tools[tool.name] = tool
        if rate_limit is not None:
            self._rate_limits[tool.name] = rate_limit

    def list_tools(self) -> list[str]:
        return sorted(self._tools)

    def get_logs(self) -> list[ToolLogEntry]:
        return list(self._logs)

    async def execute_tool(
        self,
        *,
        agent_id: str,
        tool_name: str,
        arguments: dict[str, Any] | None = None,
        timeout_seconds: float | None = None,
    ) -> Any:
        tool = self._tools.get(tool_name)
        if tool is None:
            raise ToolNotFoundError(f"tool '{tool_name}' is not registered")

        agent = await self.agent_registry.get_agent(agent_id)
        if agent is None:
            raise ToolPermissionError(f"agent '{agent_id}' does not exist")
        if tool_name not in agent.tool_names:
            raise ToolPermissionError(
                f"agent '{agent_id}' is not allowed to use '{tool_name}'"
            )

        call_args = arguments or {}
        self._enforce_rate_limit(agent_id, tool_name)

        started_at = datetime.now(timezone.utc)
        error_message: str | None = None
        success = False

        try:
            result = await asyncio.wait_for(
                tool.execute(
                    ToolContext(
                        agent_id=agent_id,
                        tool_name=tool_name,
                        arguments=call_args,
                    )
                ),
                timeout=(
                    self.default_timeout_seconds
                    if timeout_seconds is None
                    else timeout_seconds
                ),
            )
            success = True
            return result
        except TimeoutError as exc:
            error_message = f"tool '{tool_name}' timed out"
            raise TimeoutError(error_message) from exc
        except Exception as exc:
            error_message = str(exc)
            raise
        finally:
            completed_at = datetime.now(timezone.utc)
            self._logs.append(
                ToolLogEntry(
                    agent_id=agent_id,
                    tool_name=tool_name,
                    arguments=call_args,
                    success=success,
                    started_at=started_at,
                    completed_at=completed_at,
                    error=error_message,
                )
            )
            await self.event_bus.publish(
                TOOL_CALLED,
                {
                    "agent_id": agent_id,
                    "tool_name": tool_name,
                    "arguments": call_args,
                    "success": success,
                    "error": error_message,
                    "started_at": started_at.isoformat(),
                    "completed_at": completed_at.isoformat(),
                },
                correlation_id=agent_id,
            )

    def _enforce_rate_limit(self, agent_id: str, tool_name: str) -> None:
        limit = self._rate_limits.get(tool_name, self.default_rate_limit)
        if limit is None:
            return

        now = datetime.now(timezone.utc)
        window_start = now - timedelta(seconds=limit.per_seconds)
        key = (agent_id, tool_name)
        history = self._call_history.setdefault(key, deque())

        while history and history[0] <= window_start:
            history.popleft()

        if len(history) >= limit.calls:
            raise ToolRateLimitError(
                f"tool '{tool_name}' exceeded {limit.calls} calls per "
                f"{limit.per_seconds} seconds"
            )

        history.append(now)
