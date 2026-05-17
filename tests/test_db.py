import pytest

from kernel.db.session import AsyncSessionLocal


@pytest.mark.asyncio
async def test_db_connection():
    async with AsyncSessionLocal() as session:
        assert session is not None
