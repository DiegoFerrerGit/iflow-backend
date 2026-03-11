from __future__ import annotations

from bson import ObjectId

from src.core.db import get_db


async def find_user_by_id(user_id: str) -> dict | None:
    db = get_db()
    return await db.users.find_one({"_id": ObjectId(user_id)})
