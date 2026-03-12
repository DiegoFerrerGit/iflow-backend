from __future__ import annotations

import logging

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from src.core.config import settings

logger = logging.getLogger(__name__)

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


def get_db() -> AsyncIOMotorDatabase:
    if _db is None:
        raise RuntimeError("Database not initialised. Call connect_db() first.")
    return _db


async def connect_db() -> None:
    global _client, _db
    logger.info("Connecting to MongoDB")
    _client = AsyncIOMotorClient(settings.MONGODB_URI)
    _db = _client[settings.MONGODB_DB_NAME]
    await _db.command("ping")
    logger.info("Connected to MongoDB")


async def close_db() -> None:
    global _client, _db
    if _client is not None:
        _client.close()
        logger.info("MongoDB connection closed")
    _client = None
    _db = None


async def ensure_indexes() -> None:
    db = get_db()

    await db.users.create_index("googleSub", unique=True)
    await db.users.create_index("email", unique=True)
    logger.info("Ensured indexes on 'users' collection")

    await db.user_sessions.create_index("userId")
    await db.user_sessions.create_index("expiresAt")
    logger.info("Ensured indexes on 'user_sessions' collection")

    await db.allowed_emails.create_index("email", unique=True)
    logger.info("Ensured indexes on 'allowed_emails' collection")

    await db.income_sources.create_index("userId")
    logger.info("Ensured indexes on 'income_sources' collection")

    await db.allocation_boxes.create_index("userId")
    logger.info("Ensured indexes on 'allocation_boxes' collection")

    await db.allocation_subcategories.create_index(
        [("userId", 1), ("allocationBoxId", 1)]
    )
    logger.info("Ensured indexes on 'allocation_subcategories' collection")

    await db.allocation_items.create_index([("userId", 1), ("subCategoryId", 1)])
    await db.allocation_items.create_index([("userId", 1), ("allocationBoxId", 1)])
    logger.info("Ensured indexes on 'allocation_items' collection")

    await db.odin_user_state.create_index("userId", unique=True)
    logger.info("Ensured indexes on 'odin_user_state' collection")
