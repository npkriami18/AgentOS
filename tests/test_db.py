import pytest


@pytest.mark.asyncio
async def test_db_connection(db_session):
    assert db_session is not None
