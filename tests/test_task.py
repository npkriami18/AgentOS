from kernel.db.models.task import Task


async def test_task_creation(db_session):
    task = Task(title="Research vector DBs")

    db_session.add(task)

    await db_session.commit()

    assert task.id is not None
    assert task.status == "PENDING"
