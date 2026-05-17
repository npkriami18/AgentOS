from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from kernel.db.models.agent import Agent


class AgentRegistry:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self.session_factory = session_factory

    async def create_agent(
        self,
        name: str,
        role: str,
        status: str = "idle",
        description: str | None = None,
        metadata_json: dict | None = None,
        tool_names: list[str] | None = None,
    ) -> Agent:
        async with self.session_factory() as session:
            agent = Agent(
                name=name,
                role=role,
                status=status,
                description=description,
                metadata_json=metadata_json or {},
                tool_names=tool_names or [],
            )
            session.add(agent)
            await session.commit()
            await session.refresh(agent)
            return agent

    async def get_agent(self, agent_id: str) -> Agent | None:
        async with self.session_factory() as session:
            return await session.get(Agent, agent_id)

    async def list_agents(self) -> Sequence[Agent]:
        async with self.session_factory() as session:
            result = await session.execute(select(Agent).order_by(Agent.name.asc()))
            return list(result.scalars().all())

    async def update_metadata(self, agent_id: str, metadata_json: dict) -> Agent | None:
        async with self.session_factory() as session:
            agent = await session.get(Agent, agent_id)
            if agent is None:
                return None

            agent.metadata_json = metadata_json
            await session.commit()
            await session.refresh(agent)
            return agent

    async def register_tool(self, agent_id: str, tool_name: str) -> Agent | None:
        async with self.session_factory() as session:
            agent = await session.get(Agent, agent_id)
            if agent is None:
                return None

            tools = list(agent.tool_names)
            if tool_name not in tools:
                tools.append(tool_name)
                agent.tool_names = tools

            await session.commit()
            await session.refresh(agent)
            return agent

    async def unregister_tool(self, agent_id: str, tool_name: str) -> Agent | None:
        async with self.session_factory() as session:
            agent = await session.get(Agent, agent_id)
            if agent is None:
                return None

            agent.tool_names = [name for name in agent.tool_names if name != tool_name]
            await session.commit()
            await session.refresh(agent)
            return agent

    async def enable_agent(self, agent_id: str) -> Agent | None:
        return await self.set_status(agent_id, "idle")

    async def disable_agent(self, agent_id: str) -> Agent | None:
        return await self.set_status(agent_id, "disabled")

    async def set_status(self, agent_id: str, status: str) -> Agent | None:
        async with self.session_factory() as session:
            agent = await session.get(Agent, agent_id)
            if agent is None:
                return None

            agent.status = status
            await session.commit()
            await session.refresh(agent)
            return agent
