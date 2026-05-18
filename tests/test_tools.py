import asyncio
from pathlib import Path
from types import SimpleNamespace

import pytest

from kernel.tools.base import BaseTool, ToolContext
from kernel.tools.builtin import CalculatorTool, FileReaderTool, WebSearchTool
from kernel.tools.errors import ToolPermissionError, ToolRateLimitError
from kernel.tools.manager import RateLimit, ToolManager


class SlowTool(BaseTool):
    name = "slow_tool"
    description = "Sleeps longer than the timeout."

    async def execute(self, context: ToolContext) -> str:
        await asyncio.sleep(0.05)
        return "finished"


class FakeAgentRegistry:
    def __init__(self, agent_tools: dict[str, list[str]]) -> None:
        self.agent_tools = agent_tools

    async def get_agent(self, agent_id: str) -> SimpleNamespace | None:
        tools = self.agent_tools.get(agent_id)
        if tools is None:
            return None
        return SimpleNamespace(id=agent_id, tool_names=tools)


class FakeEventBus:
    def __init__(self) -> None:
        self.events: list[dict[str, object]] = []

    async def publish(
        self,
        event_type: str,
        payload: dict[str, object],
        correlation_id: str | None = None,
    ) -> dict[str, object]:
        event = {
            "type": event_type,
            "payload": payload,
            "correlation_id": correlation_id,
        }
        self.events.append(event)
        return event


@pytest.mark.asyncio
async def test_tool_manager_enforces_permissions():
    registry = FakeAgentRegistry({"agent-1": []})
    manager = ToolManager(registry, FakeEventBus())
    manager.register_tool(CalculatorTool())

    with pytest.raises(
        ToolPermissionError,
        match="agent 'agent-1' is not allowed to use 'calculator'",
    ):
        await manager.execute_tool(
            agent_id="agent-1",
            tool_name="calculator",
            arguments={"expression": "1 + 1"},
        )


@pytest.mark.asyncio
async def test_tool_manager_runs_registered_tool_and_logs_event():
    event_bus = FakeEventBus()
    registry = FakeAgentRegistry({"agent-1": ["calculator"]})
    manager = ToolManager(registry, event_bus)
    manager.register_tool(CalculatorTool())

    result = await manager.execute_tool(
        agent_id="agent-1",
        tool_name="calculator",
        arguments={"expression": "(2 + 3) * 4"},
    )

    assert result == 20
    logs = manager.get_logs()
    assert len(logs) == 1
    assert logs[0].success is True
    assert logs[0].tool_name == "calculator"
    assert len(event_bus.events) == 1
    assert event_bus.events[0]["payload"]["success"] is True


@pytest.mark.asyncio
async def test_tool_manager_enforces_timeout():
    registry = FakeAgentRegistry({"agent-1": ["slow_tool"]})
    manager = ToolManager(registry, FakeEventBus())
    manager.register_tool(SlowTool())

    with pytest.raises(TimeoutError, match="tool 'slow_tool' timed out"):
        await manager.execute_tool(
            agent_id="agent-1",
            tool_name="slow_tool",
            timeout_seconds=0.001,
        )

    logs = manager.get_logs()
    assert len(logs) == 1
    assert logs[0].success is False
    assert logs[0].error == "tool 'slow_tool' timed out"


@pytest.mark.asyncio
async def test_tool_manager_enforces_rate_limits():
    registry = FakeAgentRegistry({"agent-1": ["calculator"]})
    manager = ToolManager(
        registry,
        FakeEventBus(),
        default_rate_limit=RateLimit(calls=1, per_seconds=60),
    )
    manager.register_tool(CalculatorTool())

    result = await manager.execute_tool(
        agent_id="agent-1",
        tool_name="calculator",
        arguments={"expression": "6 / 2"},
    )

    assert result == 3

    with pytest.raises(
        ToolRateLimitError,
        match="tool 'calculator' exceeded 1 calls per 60 seconds",
    ):
        await manager.execute_tool(
            agent_id="agent-1",
            tool_name="calculator",
            arguments={"expression": "4 / 2"},
        )


@pytest.mark.asyncio
async def test_file_reader_tool_reads_within_workspace(tmp_path: Path):
    tool = FileReaderTool(tmp_path)
    file_path = tmp_path / "notes.txt"
    file_path.write_text("hello tools", encoding="utf-8")

    result = await tool.execute(
        ToolContext(
            agent_id="agent-1",
            tool_name="file_reader",
            arguments={"path": "notes.txt"},
        )
    )

    assert result == "hello tools"


@pytest.mark.asyncio
async def test_file_reader_tool_rejects_path_escape(tmp_path: Path):
    tool = FileReaderTool(tmp_path)
    outside = tmp_path.parent / "secret.txt"
    outside.write_text("nope", encoding="utf-8")

    with pytest.raises(
        PermissionError, match="file_reader path escapes the configured base path"
    ):
        await tool.execute(
            ToolContext(
                agent_id="agent-1",
                tool_name="file_reader",
                arguments={"path": "../secret.txt"},
            )
        )


@pytest.mark.asyncio
async def test_web_search_tool_uses_search_client():
    queries: list[str] = []

    async def fake_search(query: str) -> list[dict[str, str]]:
        queries.append(query)
        return [{"title": "AgentOS", "url": "https://example.com"}]

    tool = WebSearchTool(fake_search)
    results = await tool.execute(
        ToolContext(
            agent_id="agent-1",
            tool_name="web_search",
            arguments={"query": "agent orchestration"},
        )
    )

    assert queries == ["agent orchestration"]
    assert results[0]["title"] == "AgentOS"
