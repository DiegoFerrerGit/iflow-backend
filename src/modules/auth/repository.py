from __future__ import annotations

from datetime import datetime, timezone

from bson import ObjectId
from pymongo import ReturnDocument

from src.core.db import get_db


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

async def upsert_user(
    google_sub: str,
    email: str,
    full_name: str | None,
    avatar_url: str | None,
) -> dict:
    db = get_db()
    now = datetime.now(timezone.utc)

    user = await db.users.find_one_and_update(
        {"googleSub": google_sub},
        {
            "$set": {
                "email": email,
                "fullName": full_name,
                "avatarUrl": avatar_url,
                "updatedAt": now,
            },
            "$setOnInsert": {
                "googleSub": google_sub,
                "preferences": {"displayCurrency": "USD"},
                "createdAt": now,
            },
        },
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    return user


async def find_user_by_id(user_id: str) -> dict | None:
    db = get_db()
    return await db.users.find_one({"_id": ObjectId(user_id)})


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------

async def create_session(
    user_id: ObjectId,
    refresh_token_hash: str,
    expires_at: datetime,
) -> None:
    db = get_db()
    await db.user_sessions.insert_one(
        {
            "userId": user_id,
            "refreshTokenHash": refresh_token_hash,
            "expiresAt": expires_at,
            "createdAt": datetime.now(timezone.utc),
            "revokedAt": None,
        }
    )


async def find_valid_session(refresh_token_hash: str) -> dict | None:
    db = get_db()
    now = datetime.now(timezone.utc)
    return await db.user_sessions.find_one(
        {
            "refreshTokenHash": refresh_token_hash,
            "revokedAt": None,
            "expiresAt": {"$gt": now},
        }
    )


async def rotate_session(
    session_id: ObjectId,
    new_hash: str,
    new_expires_at: datetime,
) -> None:
    db = get_db()
    await db.user_sessions.update_one(
        {"_id": session_id},
        {
            "$set": {
                "refreshTokenHash": new_hash,
                "expiresAt": new_expires_at,
            }
        },
    )


async def revoke_session(refresh_token_hash: str) -> None:
    db = get_db()
    await db.user_sessions.update_one(
        {"refreshTokenHash": refresh_token_hash, "revokedAt": None},
        {"$set": {"revokedAt": datetime.now(timezone.utc)}},
    )
