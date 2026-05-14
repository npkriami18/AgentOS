from kernel.db.models.agent import Agent


async def test_agent_creation(db_session):
    agent = Agent(
        name="ResearchAgent",
        role="research"
    )

    db_session.add(agent)

    await db_session.commit()

    assert agent.id is not None