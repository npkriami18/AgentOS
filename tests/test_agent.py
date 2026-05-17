import pytest
from sqlalchemy import delete

from kernel.db.models.agent import Agent
from kernel.db.session import AsyncSessionLocal


async def clear_agents() -> None:
    async with AsyncSessionLocal() as session:
        await session.execute(delete(Agent))
        await session.commit()


@pytest.mark.asyncio
async def test_agent_creation():
    await clear_agents()

    async with AsyncSessionLocal() as session:
        agent = Agent(
            name="ResearchAgent",
            role="research",
        )

        session.add(agent)
        await session.commit()
        await session.refresh(agent)

        assert agent.id is not None
        assert agent.status == "idle"
