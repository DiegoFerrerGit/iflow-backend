import pytest_asyncio

from src.core.db import close_db, connect_db, ensure_indexes
from src.core.log import setup_logging

setup_logging()


@pytest_asyncio.fixture(autouse=True)
async def _setup_db():
    await connect_db()
    await ensure_indexes()
    yield
    await close_db()
