import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from kernel.db.session import AsyncSessionLocal


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()
