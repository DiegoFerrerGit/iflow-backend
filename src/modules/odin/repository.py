from __future__ import annotations

from datetime import datetime, timezone

from bson import ObjectId
from pymongo import ReturnDocument

from src.core.db import get_db


# ---------------------------------------------------------------------------
# Income sources
# ---------------------------------------------------------------------------

async def find_income_sources_by_user(user_id: str) -> list[dict]:
    db = get_db()
    cursor = db.income_sources.find({"userId": ObjectId(user_id)})
    return await cursor.to_list(length=None)


async def find_income_source(income_source_id: str, user_id: str) -> dict | None:
    db = get_db()
    return await db.income_sources.find_one(
        {"_id": ObjectId(income_source_id), "userId": ObjectId(user_id)}
    )


async def create_income_source(user_id: str, data: dict) -> dict:
    db = get_db()
    now = datetime.now(timezone.utc)
    doc = {**data, "userId": ObjectId(user_id), "createdAt": now, "updatedAt": now}
    result = await db.income_sources.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


async def update_income_source(
    income_source_id: str, user_id: str, data: dict
) -> dict | None:
    db = get_db()
    return await db.income_sources.find_one_and_update(
        {"_id": ObjectId(income_source_id), "userId": ObjectId(user_id)},
        {"$set": {**data, "updatedAt": datetime.now(timezone.utc)}},
        return_document=ReturnDocument.AFTER,
    )


async def delete_income_source(income_source_id: str, user_id: str) -> bool:
    db = get_db()
    r = await db.income_sources.delete_one(
        {"_id": ObjectId(income_source_id), "userId": ObjectId(user_id)}
    )
    return r.deleted_count > 0


# ---------------------------------------------------------------------------
# Allocation boxes
# ---------------------------------------------------------------------------

async def find_allocation_boxes_by_user(user_id: str) -> list[dict]:
    db = get_db()
    cursor = db.allocation_boxes.find({"userId": ObjectId(user_id)})
    return await cursor.to_list(length=None)


async def find_allocation_box(box_id: str, user_id: str) -> dict | None:
    db = get_db()
    return await db.allocation_boxes.find_one(
        {"_id": ObjectId(box_id), "userId": ObjectId(user_id)}
    )


async def create_allocation_box(user_id: str, data: dict) -> dict:
    db = get_db()
    now = datetime.now(timezone.utc)
    doc = {**data, "userId": ObjectId(user_id), "createdAt": now, "updatedAt": now}
    result = await db.allocation_boxes.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


async def update_allocation_box(
    box_id: str, user_id: str, data: dict
) -> dict | None:
    db = get_db()
    return await db.allocation_boxes.find_one_and_update(
        {"_id": ObjectId(box_id), "userId": ObjectId(user_id)},
        {"$set": {**data, "updatedAt": datetime.now(timezone.utc)}},
        return_document=ReturnDocument.AFTER,
    )


async def delete_allocation_box(box_id: str, user_id: str) -> bool:
    db = get_db()
    r = await db.allocation_boxes.delete_one(
        {"_id": ObjectId(box_id), "userId": ObjectId(user_id)}
    )
    return r.deleted_count > 0


# ---------------------------------------------------------------------------
# Allocation subcategories
# ---------------------------------------------------------------------------

async def find_all_subcategories_by_user(user_id: str) -> list[dict]:
    db = get_db()
    cursor = db.allocation_subcategories.find({"userId": ObjectId(user_id)})
    return await cursor.to_list(length=None)


async def find_subcategories_by_box(user_id: str, box_id: str) -> list[dict]:
    db = get_db()
    cursor = db.allocation_subcategories.find(
        {"userId": ObjectId(user_id), "allocationBoxId": ObjectId(box_id)}
    )
    return await cursor.to_list(length=None)


async def find_subcategory(
    sub_id: str, user_id: str, box_id: str
) -> dict | None:
    db = get_db()
    return await db.allocation_subcategories.find_one(
        {
            "_id": ObjectId(sub_id),
            "userId": ObjectId(user_id),
            "allocationBoxId": ObjectId(box_id),
        }
    )


async def create_subcategory(user_id: str, box_id: str, data: dict) -> dict:
    db = get_db()
    now = datetime.now(timezone.utc)
    doc = {
        **data,
        "userId": ObjectId(user_id),
        "allocationBoxId": ObjectId(box_id),
        "createdAt": now,
        "updatedAt": now,
    }
    result = await db.allocation_subcategories.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


async def update_subcategory(
    sub_id: str, user_id: str, box_id: str, data: dict
) -> dict | None:
    db = get_db()
    return await db.allocation_subcategories.find_one_and_update(
        {
            "_id": ObjectId(sub_id),
            "userId": ObjectId(user_id),
            "allocationBoxId": ObjectId(box_id),
        },
        {"$set": {**data, "updatedAt": datetime.now(timezone.utc)}},
        return_document=ReturnDocument.AFTER,
    )


async def delete_subcategory(sub_id: str, user_id: str, box_id: str) -> bool:
    db = get_db()
    r = await db.allocation_subcategories.delete_one(
        {
            "_id": ObjectId(sub_id),
            "userId": ObjectId(user_id),
            "allocationBoxId": ObjectId(box_id),
        }
    )
    return r.deleted_count > 0


async def delete_subcategories_by_box(user_id: str, box_id: str) -> None:
    db = get_db()
    await db.allocation_subcategories.delete_many(
        {"userId": ObjectId(user_id), "allocationBoxId": ObjectId(box_id)}
    )


# ---------------------------------------------------------------------------
# Allocation items
# ---------------------------------------------------------------------------

async def find_all_items_by_user(user_id: str) -> list[dict]:
    db = get_db()
    cursor = db.allocation_items.find({"userId": ObjectId(user_id)})
    return await cursor.to_list(length=None)


async def find_items_by_subcategory(user_id: str, sub_id: str) -> list[dict]:
    db = get_db()
    cursor = db.allocation_items.find(
        {"userId": ObjectId(user_id), "subCategoryId": ObjectId(sub_id)}
    )
    return await cursor.to_list(length=None)


async def find_item(
    item_id: str, user_id: str, sub_id: str
) -> dict | None:
    db = get_db()
    return await db.allocation_items.find_one(
        {
            "_id": ObjectId(item_id),
            "userId": ObjectId(user_id),
            "subCategoryId": ObjectId(sub_id),
        }
    )


async def create_item(
    user_id: str, box_id: str, sub_id: str, data: dict
) -> dict:
    db = get_db()
    now = datetime.now(timezone.utc)
    doc = {
        **data,
        "userId": ObjectId(user_id),
        "allocationBoxId": ObjectId(box_id),
        "subCategoryId": ObjectId(sub_id),
        "createdAt": now,
        "updatedAt": now,
    }
    result = await db.allocation_items.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


async def update_item(
    item_id: str, user_id: str, sub_id: str, data: dict
) -> dict | None:
    db = get_db()
    return await db.allocation_items.find_one_and_update(
        {
            "_id": ObjectId(item_id),
            "userId": ObjectId(user_id),
            "subCategoryId": ObjectId(sub_id),
        },
        {"$set": {**data, "updatedAt": datetime.now(timezone.utc)}},
        return_document=ReturnDocument.AFTER,
    )


async def delete_item(item_id: str, user_id: str, sub_id: str) -> bool:
    db = get_db()
    r = await db.allocation_items.delete_one(
        {
            "_id": ObjectId(item_id),
            "userId": ObjectId(user_id),
            "subCategoryId": ObjectId(sub_id),
        }
    )
    return r.deleted_count > 0


async def delete_items_by_subcategory(user_id: str, sub_id: str) -> None:
    db = get_db()
    await db.allocation_items.delete_many(
        {"userId": ObjectId(user_id), "subCategoryId": ObjectId(sub_id)}
    )


async def delete_items_by_box(user_id: str, box_id: str) -> None:
    db = get_db()
    await db.allocation_items.delete_many(
        {"userId": ObjectId(user_id), "allocationBoxId": ObjectId(box_id)}
    )


# ---------------------------------------------------------------------------
# ODIN onboarding state
# ---------------------------------------------------------------------------

async def get_odin_onboarding_completed(user_id: str) -> bool:
    db = get_db()
    doc = await db.odin_user_state.find_one({"userId": ObjectId(user_id)})
    return bool(doc and doc.get("odinOnboardingCompleted"))


async def set_odin_onboarding_completed(user_id: str) -> None:
    db = get_db()
    now = datetime.now(timezone.utc)
    await db.odin_user_state.update_one(
        {"userId": ObjectId(user_id)},
        {
            "$set": {
                "odinOnboardingCompleted": True,
                "updatedAt": now,
            }
        },
        upsert=True,
    )
