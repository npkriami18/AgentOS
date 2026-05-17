import pytest
from sqlalchemy import delete

from kernel.agents.registry import AgentRegistry
from kernel.db.models.agent import Agent
from kernel.db.session import AsyncSessionLocal


async def clear_agents() -> None:
    async with AsyncSessionLocal() as session:
        await session.execute(delete(Agent))
        await session.commit()


@pytest.mark.asyncio
async def test_create_agent_with_metadata_and_tools():
    await clear_agents()

    registry = AgentRegistry(AsyncSessionLocal)

    agent = await registry.create_agent(
        name="Planner",
        role="planning",
        description="Plans task execution",
        metadata_json={"team": "core"},
        tool_names=["calculator"],
    )

    assert agent.id is not None
    assert agent.description == "Plans task execution"
    assert agent.metadata_json["team"] == "core"
    assert agent.tool_names == ["calculator"]


@pytest.mark.asyncio
async def test_register_tool():
    await clear_agents()

    registry = AgentRegistry(AsyncSessionLocal)
    agent = await registry.create_agent(name="Researcher", role="research")

    updated = await registry.register_tool(agent.id, "web_search")

    assert updated is not None
    assert "web_search" in updated.tool_names


@pytest.mark.asyncio
async def test_disable_agent():
    await clear_agents()

    registry = AgentRegistry(AsyncSessionLocal)
    agent = await registry.create_agent(name="Writer", role="writing")

    updated = await registry.disable_agent(agent.id)

    assert updated is not None
    assert updated.status == "disabled"
