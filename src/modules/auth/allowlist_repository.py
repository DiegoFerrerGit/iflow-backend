from __future__ import annotations

from datetime import datetime, timezone

from pymongo import ReturnDocument

from src.core.db import get_db


async def upsert_allowed_email(email: str) -> dict:
    db = get_db()
    now = datetime.now(timezone.utc)

    return await db.allowed_emails.find_one_and_update(
        {"email": email},
        {
            "$set": {
                "enabled": True,
                "updatedAt": now,
            },
            "$setOnInsert": {
                "email": email,
                "createdAt": now,
            },
        },
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )


async def is_email_allowed(email: str) -> bool:
    db = get_db()
    doc = await db.allowed_emails.find_one(
        {"email": email, "enabled": True},
        {"_id": 1},
    )
    return doc is not None
