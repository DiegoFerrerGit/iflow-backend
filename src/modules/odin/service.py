from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from src.core.config import settings
from src.core.errors import OdinErrorCodes, business_error, not_found_error
from src.modules.currency import service as currency_service
from src.modules.odin import repository as repo
from src.modules.odin.schemas import (
    AllocationBoxDetailResponse,
    AllocationBoxDto,
    AllocationItemDto,
    AllocationSubCategoryDto,
    AmountWithCurrency,
    IncomeSourceCreate,
    IncomeSourceDto,
    IncomeSourceUpdate,
    AllocationBoxCreate,
    AllocationBoxUpdate,
    ItemCreate,
    ItemUpdate,
    OdinOverviewResponse,
    PoolSummary,
    SubCategoryCreate,
    SubCategoryDetailResponse,
    SubCategoryUpdate,
)

logger = logging.getLogger(__name__)


async def _simulate_delay() -> None:
    delay = settings.API_DELAY_SECONDS
    if delay > 0:
        await asyncio.sleep(delay)


async def _get_exchange_rate() -> float:
    """Use live rate from currency API; fallback to config if unavailable."""
    rate, _ = await currency_service.get_rate_for_display()
    return rate


# ---------------------------------------------------------------------------
# Private helpers – conversion
# ---------------------------------------------------------------------------

def _to_usd(amount: float, currency: str, rate: float) -> float:
    if currency == "USD":
        return amount
    return amount / rate


def _group_by(docs: list[dict], field: str) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = {}
    for doc in docs:
        key = str(doc[field])
        groups.setdefault(key, []).append(doc)
    return groups


def _nested_amount(doc: dict, prefix: str) -> AmountWithCurrency | None:
    amt = doc.get(f"{prefix}Amount")
    cur = doc.get(f"{prefix}Currency")
    if amt is not None and cur is not None:
        return AmountWithCurrency(amount=amt, currency=cur)
    return None


# ---------------------------------------------------------------------------
# Private helpers – computation (pure, no DB)
# ---------------------------------------------------------------------------

def _compute_box_amount(
    box: dict,
    pool_total: float,
    subs_by_box: dict[str, list[dict]],
    items_by_sub: dict[str, list[dict]],
    rate: float,
) -> float:
    if box["calculationType"] == "percentage":
        return pool_total * (box.get("percentageOfPool", 0) / 100)
    return _sum_subs_usd(
        subs_by_box.get(str(box["_id"]), []), items_by_sub, rate
    )


def _sum_subs_usd(
    subs: list[dict],
    items_by_sub: dict[str, list[dict]],
    rate: float,
) -> float:
    total = 0.0
    for sub in subs:
        if sub["type"] == "fixed_amount":
            total += _to_usd(
                sub.get("fixedAmount", 0),
                sub.get("fixedCurrency", "USD"),
                rate,
            )
        else:
            for item in items_by_sub.get(str(sub["_id"]), []):
                total += _to_usd(item["amount"], item["currency"], rate)
    return total


# ---------------------------------------------------------------------------
# Private helpers – DTO conversion
# ---------------------------------------------------------------------------

def _income_dto(doc: dict) -> IncomeSourceDto:
    return IncomeSourceDto(
        id=str(doc["_id"]),
        name=doc["name"],
        role=doc["role"],
        effort_percentage=doc["effortPercentage"],
        icon=doc.get("icon"),
        color=doc["color"],
        category=doc["category"],
        amount_with_currency=AmountWithCurrency(
            amount=doc["amount"], currency=doc["currency"]
        ),
    )


def _box_dto(doc: dict, calculated_usd: float) -> AllocationBoxDto:
    return AllocationBoxDto(
        id=str(doc["_id"]),
        name=doc["name"],
        description=doc["description"],
        type=doc["type"],
        calculation_type=doc["calculationType"],
        percentage_of_pool=doc.get("percentageOfPool"),
        saved_amount=_nested_amount(doc, "savedAmount"),
        savings_target=_nested_amount(doc, "savingsTarget"),
        icon=doc["icon"],
        color=doc["color"],
        calculated_amount_in_usd=round(calculated_usd, 2),
    )


def _sub_dto(doc: dict, display: AmountWithCurrency) -> AllocationSubCategoryDto:
    return AllocationSubCategoryDto(
        id=str(doc["_id"]),
        allocation_box_id=str(doc["allocationBoxId"]),
        name=doc["name"],
        type=doc["type"],
        icon=doc.get("icon"),
        color=doc.get("color"),
        display_amount=display,
    )


def _item_dto(doc: dict) -> AllocationItemDto:
    has_control = doc.get("hasPaymentControl", False)
    paid: bool | None = None
    if has_control:
        current_month = datetime.now(timezone.utc).strftime("%Y-%m")
        paid = doc.get("paidMonth") == current_month
    return AllocationItemDto(
        id=str(doc["_id"]),
        sub_category_id=str(doc["subCategoryId"]),
        name=doc["name"],
        description=doc.get("description"),
        icon=doc.get("icon"),
        color=doc.get("color"),
        amount_with_currency=AmountWithCurrency(
            amount=doc["amount"], currency=doc["currency"]
        ),
        has_payment_control=has_control,
        paid=paid,
    )


# ---------------------------------------------------------------------------
# Private helpers – async (fetch + compute)
# ---------------------------------------------------------------------------

async def _pool_total_usd(user_id: str, rate: float) -> float:
    sources = await repo.find_income_sources_by_user(user_id)
    return sum(_to_usd(s["amount"], s["currency"], rate) for s in sources)


async def _pool_summary(user_id: str, rate: float) -> PoolSummary:
    sources = await repo.find_income_sources_by_user(user_id)
    boxes = await repo.find_allocation_boxes_by_user(user_id)
    all_subs = await repo.find_all_subcategories_by_user(user_id)
    all_items = await repo.find_all_items_by_user(user_id)

    total = sum(_to_usd(s["amount"], s["currency"], rate) for s in sources)
    subs_by_box = _group_by(all_subs, "allocationBoxId")
    items_by_sub = _group_by(all_items, "subCategoryId")

    assigned = sum(
        _compute_box_amount(b, total, subs_by_box, items_by_sub, rate)
        for b in boxes
    )
    return PoolSummary(
        total_amount_in_usd=round(total, 2),
        assigned_amount_in_usd=round(assigned, 2),
        unassigned_amount_in_usd=round(total - assigned, 2),
    )


async def _build_box_dto(box: dict, user_id: str, rate: float) -> AllocationBoxDto:
    if box["calculationType"] == "percentage":
        pool_total = await _pool_total_usd(user_id, rate)
        calc = pool_total * (box.get("percentageOfPool", 0) / 100)
    else:
        subs = await repo.find_subcategories_by_box(user_id, str(box["_id"]))
        items_by_sub: dict[str, list[dict]] = {}
        for sub in subs:
            items = await repo.find_items_by_subcategory(user_id, str(sub["_id"]))
            items_by_sub[str(sub["_id"])] = items
        calc = _sum_subs_usd(subs, items_by_sub, rate)
    return _box_dto(box, calc)


async def _build_sub_dto(
    sub: dict, user_id: str, rate: float
) -> AllocationSubCategoryDto:
    if sub["type"] == "fixed_amount":
        display = AmountWithCurrency(
            amount=sub.get("fixedAmount", 0),
            currency=sub.get("fixedCurrency", "USD"),
        )
    else:
        items = await repo.find_items_by_subcategory(user_id, str(sub["_id"]))
        total = sum(_to_usd(i["amount"], i["currency"], rate) for i in items)
        display = AmountWithCurrency(amount=round(total, 2), currency="USD")
    return _sub_dto(sub, display)


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

async def _validate_percentage_budget(
    user_id: str, new_pct: float, exclude_box_id: str | None = None
) -> None:
    boxes = await repo.find_allocation_boxes_by_user(user_id)
    current = sum(
        b.get("percentageOfPool", 0)
        for b in boxes
        if b["calculationType"] == "percentage"
        and (exclude_box_id is None or str(b["_id"]) != exclude_box_id)
    )
    if current + new_pct > 100:
        raise business_error(
            OdinErrorCodes.PERCENTAGE_EXCEEDS_LIMIT,
            f"Total percentage would be {current + new_pct}%, exceeding 100%.",
        )


async def _require_box(user_id: str, box_id: str) -> dict:
    box = await repo.find_allocation_box(box_id, user_id)
    if not box:
        raise not_found_error(
            OdinErrorCodes.ALLOCATION_BOX_NOT_FOUND,
            "The allocation box was not found.",
        )
    return box


async def _require_subcategory(user_id: str, box_id: str, sub_id: str) -> dict:
    sub = await repo.find_subcategory(sub_id, user_id, box_id)
    if not sub:
        raise not_found_error(
            OdinErrorCodes.SUBCATEGORY_NOT_FOUND,
            "The subcategory was not found.",
        )
    return sub


async def _require_item(user_id: str, sub_id: str, item_id: str) -> dict:
    item = await repo.find_item(item_id, user_id, sub_id)
    if not item:
        raise not_found_error(
            OdinErrorCodes.ITEM_NOT_FOUND,
            "The item was not found.",
        )
    return item


# ---------------------------------------------------------------------------
# Overview
# ---------------------------------------------------------------------------

async def get_overview(user_id: str) -> OdinOverviewResponse:
    await _simulate_delay()
    rate = await _get_exchange_rate()

    sources = await repo.find_income_sources_by_user(user_id)
    boxes = await repo.find_allocation_boxes_by_user(user_id)
    all_subs = await repo.find_all_subcategories_by_user(user_id)
    all_items = await repo.find_all_items_by_user(user_id)

    total = sum(_to_usd(s["amount"], s["currency"], rate) for s in sources)
    subs_by_box = _group_by(all_subs, "allocationBoxId")
    items_by_sub = _group_by(all_items, "subCategoryId")

    assigned = 0.0
    box_dtos: list[AllocationBoxDto] = []
    for box in boxes:
        calc = _compute_box_amount(box, total, subs_by_box, items_by_sub, rate)
        assigned += calc
        box_dtos.append(_box_dto(box, calc))

    onboarding_completed = await repo.get_odin_onboarding_completed(user_id)
    odin_onboarding = not onboarding_completed

    return OdinOverviewResponse(
        pool_summary=PoolSummary(
            total_amount_in_usd=round(total, 2),
            assigned_amount_in_usd=round(assigned, 2),
            unassigned_amount_in_usd=round(total - assigned, 2),
        ),
        income_sources=[_income_dto(s) for s in sources],
        allocation_boxes=box_dtos,
        odin_onboarding=odin_onboarding,
    )


# ---------------------------------------------------------------------------
# Onboarding
# ---------------------------------------------------------------------------

async def mark_onboarding_completed(user_id: str) -> None:
    sources = await repo.find_income_sources_by_user(user_id)
    boxes = await repo.find_allocation_boxes_by_user(user_id)

    if len(sources) < 1:
        raise business_error(
            OdinErrorCodes.ONBOARDING_PREREQUISITES_NOT_MET,
            "You must add at least one income source before completing onboarding.",
        )
    if len(boxes) < 1:
        raise business_error(
            OdinErrorCodes.ONBOARDING_PREREQUISITES_NOT_MET,
            "You must add at least one allocation box before completing onboarding.",
        )

    await repo.set_odin_onboarding_completed(user_id)


# ---------------------------------------------------------------------------
# Box detail (level 2)
# ---------------------------------------------------------------------------

async def get_box_detail(
    user_id: str, box_id: str
) -> AllocationBoxDetailResponse:
    await _simulate_delay()
    rate = await _get_exchange_rate()
    box = await _require_box(user_id, box_id)
    subs = await repo.find_subcategories_by_box(user_id, box_id)

    items_by_sub: dict[str, list[dict]] = {}
    for sub in subs:
        items = await repo.find_items_by_subcategory(user_id, str(sub["_id"]))
        items_by_sub[str(sub["_id"])] = items

    if box["calculationType"] == "percentage":
        pool_total = await _pool_total_usd(user_id, rate)
        box_budget = pool_total * (box.get("percentageOfPool", 0) / 100)
        subs_total = _sum_subs_usd(subs, items_by_sub, rate)
        available = max(0.0, box_budget - subs_total)
    else:
        summary = await _pool_summary(user_id, rate)
        available = max(0.0, summary.unassigned_amount_in_usd)

    sub_dtos: list[AllocationSubCategoryDto] = []
    for sub in subs:
        if sub["type"] == "fixed_amount":
            display = AmountWithCurrency(
                amount=sub.get("fixedAmount", 0),
                currency=sub.get("fixedCurrency", "USD"),
            )
        else:
            sub_items = items_by_sub.get(str(sub["_id"]), [])
            total_usd = sum(
                _to_usd(i["amount"], i["currency"], rate) for i in sub_items
            )
            display = AmountWithCurrency(amount=round(total_usd, 2), currency="USD")
        sub_dtos.append(_sub_dto(sub, display))

    return AllocationBoxDetailResponse(
        allocation_box_id=str(box["_id"]),
        allocation_box_name=box["name"],
        allocation_box_type=box["type"],
        allocation_box_calculation_type=box["calculationType"],
        available_amount_to_assign=round(available, 2),
        sub_categories=sub_dtos,
    )


# ---------------------------------------------------------------------------
# Subcategory detail (level 3)
# ---------------------------------------------------------------------------

async def get_subcategory_detail(
    user_id: str, box_id: str, sub_id: str
) -> SubCategoryDetailResponse:
    await _simulate_delay()
    rate = await _get_exchange_rate()
    box = await _require_box(user_id, box_id)
    sub = await _require_subcategory(user_id, box_id, sub_id)

    items = await repo.find_items_by_subcategory(user_id, sub_id)

    if box["calculationType"] == "percentage":
        pool_total = await _pool_total_usd(user_id, rate)
        box_budget = pool_total * (box.get("percentageOfPool", 0) / 100)
        subs = await repo.find_subcategories_by_box(user_id, box_id)
        items_by_sub: dict[str, list[dict]] = {}
        for s in subs:
            items_by_sub[str(s["_id"])] = await repo.find_items_by_subcategory(
                user_id, str(s["_id"])
            )
        subs_total = _sum_subs_usd(subs, items_by_sub, rate)
        available = max(0.0, box_budget - subs_total)
    else:
        summary = await _pool_summary(user_id, rate)
        available = max(0.0, summary.unassigned_amount_in_usd)

    return SubCategoryDetailResponse(
        allocation_box_id=str(box["_id"]),
        allocation_box_name=box["name"],
        allocation_box_type=box["type"],
        allocation_box_calculation_type=box["calculationType"],
        sub_category_id=str(sub["_id"]),
        sub_category_name=sub["name"],
        available_amount_to_assign=round(available, 2),
        items=[_item_dto(i) for i in items],
    )


# ---------------------------------------------------------------------------
# Income sources CRUD
# ---------------------------------------------------------------------------

async def list_income_sources(user_id: str) -> list[IncomeSourceDto]:
    await _simulate_delay()
    docs = await repo.find_income_sources_by_user(user_id)
    return [_income_dto(d) for d in docs]


async def create_income_source(
    user_id: str, data: IncomeSourceCreate
) -> IncomeSourceDto:
    await _simulate_delay()
    doc = await repo.create_income_source(user_id, {
        "name": data.name,
        "role": data.role,
        "effortPercentage": data.effort_percentage,
        "icon": data.icon,
        "color": data.color,
        "category": data.category,
        "amount": data.amount_with_currency.amount,
        "currency": data.amount_with_currency.currency,
    })
    logger.info("Income source created: %s", doc["_id"])
    return _income_dto(doc)


async def update_income_source(
    user_id: str, income_source_id: str, data: IncomeSourceUpdate
) -> IncomeSourceDto:
    await _simulate_delay()
    doc = await repo.update_income_source(income_source_id, user_id, {
        "name": data.name,
        "role": data.role,
        "effortPercentage": data.effort_percentage,
        "icon": data.icon,
        "color": data.color,
        "category": data.category,
        "amount": data.amount_with_currency.amount,
        "currency": data.amount_with_currency.currency,
    })
    if not doc:
        raise not_found_error(
            OdinErrorCodes.INCOME_SOURCE_NOT_FOUND,
            "The income source was not found.",
        )
    return _income_dto(doc)


async def delete_income_source(user_id: str, income_source_id: str) -> None:
    await _simulate_delay()
    if not await repo.delete_income_source(income_source_id, user_id):
        raise not_found_error(
            OdinErrorCodes.INCOME_SOURCE_NOT_FOUND,
            "The income source was not found.",
        )


# ---------------------------------------------------------------------------
# Allocation boxes CRUD
# ---------------------------------------------------------------------------

def _box_to_doc(data: AllocationBoxCreate | AllocationBoxUpdate) -> dict:
    doc: dict = {
        "name": data.name,
        "description": data.description,
        "type": data.type,
        "calculationType": data.calculation_type,
        "icon": data.icon,
        "color": data.color,
        "percentageOfPool": data.percentage_of_pool,
    }
    if data.type == "temporary":
        doc["savedAmountAmount"] = (
            data.saved_amount.amount if data.saved_amount else None
        )
        doc["savedAmountCurrency"] = (
            data.saved_amount.currency if data.saved_amount else None
        )
        doc["savingsTargetAmount"] = (
            data.savings_target.amount if data.savings_target else None
        )
        doc["savingsTargetCurrency"] = (
            data.savings_target.currency if data.savings_target else None
        )
    else:
        doc["savedAmountAmount"] = None
        doc["savedAmountCurrency"] = None
        doc["savingsTargetAmount"] = None
        doc["savingsTargetCurrency"] = None
    return doc


async def list_allocation_boxes(user_id: str) -> list[AllocationBoxDto]:
    await _simulate_delay()
    rate = await _get_exchange_rate()
    sources = await repo.find_income_sources_by_user(user_id)
    boxes = await repo.find_allocation_boxes_by_user(user_id)
    all_subs = await repo.find_all_subcategories_by_user(user_id)
    all_items = await repo.find_all_items_by_user(user_id)

    total = sum(_to_usd(s["amount"], s["currency"], rate) for s in sources)
    subs_by_box = _group_by(all_subs, "allocationBoxId")
    items_by_sub = _group_by(all_items, "subCategoryId")

    return [
        _box_dto(b, _compute_box_amount(b, total, subs_by_box, items_by_sub, rate))
        for b in boxes
    ]


async def create_allocation_box(
    user_id: str, data: AllocationBoxCreate
) -> AllocationBoxDto:
    await _simulate_delay()
    if data.calculation_type == "percentage":
        await _validate_percentage_budget(user_id, data.percentage_of_pool)

    doc = await repo.create_allocation_box(user_id, _box_to_doc(data))
    logger.info("Allocation box created: %s", doc["_id"])
    rate = await _get_exchange_rate()
    return await _build_box_dto(doc, user_id, rate)


async def update_allocation_box(
    user_id: str, box_id: str, data: AllocationBoxUpdate
) -> AllocationBoxDto:
    await _simulate_delay()
    await _require_box(user_id, box_id)

    if data.calculation_type == "percentage":
        await _validate_percentage_budget(
            user_id, data.percentage_of_pool, exclude_box_id=box_id
        )

    doc = await repo.update_allocation_box(box_id, user_id, _box_to_doc(data))
    if not doc:
        raise not_found_error(
            OdinErrorCodes.ALLOCATION_BOX_NOT_FOUND,
            "The allocation box was not found.",
        )
    rate = await _get_exchange_rate()
    return await _build_box_dto(doc, user_id, rate)


async def delete_allocation_box(user_id: str, box_id: str) -> None:
    await _simulate_delay()
    if not await repo.delete_allocation_box(box_id, user_id):
        raise not_found_error(
            OdinErrorCodes.ALLOCATION_BOX_NOT_FOUND,
            "The allocation box was not found.",
        )
    await repo.delete_items_by_box(user_id, box_id)
    await repo.delete_subcategories_by_box(user_id, box_id)
    logger.info("Allocation box deleted (cascade): %s", box_id)


# ---------------------------------------------------------------------------
# Subcategories CRUD
# ---------------------------------------------------------------------------

def _sub_to_doc(data: SubCategoryCreate | SubCategoryUpdate) -> dict:
    return {
        "name": data.name,
        "type": data.type,
        "fixedAmount": data.fixed_amount,
        "fixedCurrency": data.fixed_currency,
        "icon": data.icon,
        "color": data.color,
    }


async def create_subcategory(
    user_id: str, box_id: str, data: SubCategoryCreate
) -> AllocationSubCategoryDto:
    await _simulate_delay()
    await _require_box(user_id, box_id)
    doc = await repo.create_subcategory(user_id, box_id, _sub_to_doc(data))
    logger.info("Subcategory created: %s", doc["_id"])
    rate = await _get_exchange_rate()
    return await _build_sub_dto(doc, user_id, rate)


async def update_subcategory(
    user_id: str, box_id: str, sub_id: str, data: SubCategoryUpdate
) -> AllocationSubCategoryDto:
    await _simulate_delay()
    await _require_subcategory(user_id, box_id, sub_id)
    doc = await repo.update_subcategory(sub_id, user_id, box_id, _sub_to_doc(data))
    if not doc:
        raise not_found_error(
            OdinErrorCodes.SUBCATEGORY_NOT_FOUND,
            "The subcategory was not found.",
        )
    rate = await _get_exchange_rate()
    return await _build_sub_dto(doc, user_id, rate)


async def delete_subcategory(
    user_id: str, box_id: str, sub_id: str
) -> None:
    await _simulate_delay()
    if not await repo.delete_subcategory(sub_id, user_id, box_id):
        raise not_found_error(
            OdinErrorCodes.SUBCATEGORY_NOT_FOUND,
            "The subcategory was not found.",
        )
    await repo.delete_items_by_subcategory(user_id, sub_id)
    logger.info("Subcategory deleted (cascade): %s", sub_id)


# ---------------------------------------------------------------------------
# Items CRUD
# ---------------------------------------------------------------------------

def _item_to_doc(data: ItemCreate | ItemUpdate) -> dict:
    return {
        "name": data.name,
        "description": data.description,
        "icon": data.icon,
        "color": data.color,
        "amount": data.amount_with_currency.amount,
        "currency": data.amount_with_currency.currency,
        "hasPaymentControl": data.has_payment_control,
    }


async def create_item(
    user_id: str, box_id: str, sub_id: str, data: ItemCreate
) -> AllocationItemDto:
    await _simulate_delay()
    await _require_box(user_id, box_id)
    await _require_subcategory(user_id, box_id, sub_id)
    doc = await repo.create_item(user_id, box_id, sub_id, _item_to_doc(data))
    logger.info("Item created: %s", doc["_id"])
    return _item_dto(doc)


async def update_item(
    user_id: str, box_id: str, sub_id: str, item_id: str, data: ItemUpdate
) -> AllocationItemDto:
    await _simulate_delay()
    await _require_subcategory(user_id, box_id, sub_id)
    doc = await repo.update_item(item_id, user_id, sub_id, _item_to_doc(data))
    if not doc:
        raise not_found_error(OdinErrorCodes.ITEM_NOT_FOUND, "The item was not found.")
    return _item_dto(doc)


async def delete_item(
    user_id: str, box_id: str, sub_id: str, item_id: str
) -> None:
    await _simulate_delay()
    await _require_subcategory(user_id, box_id, sub_id)
    if not await repo.delete_item(item_id, user_id, sub_id):
        raise not_found_error(OdinErrorCodes.ITEM_NOT_FOUND, "The item was not found.")


async def toggle_item_paid(
    user_id: str, box_id: str, sub_id: str, item_id: str
) -> AllocationItemDto:
    await _simulate_delay()
    await _require_subcategory(user_id, box_id, sub_id)
    item = await _require_item(user_id, sub_id, item_id)

    current_month = datetime.now(timezone.utc).strftime("%Y-%m")
    new_paid_month = None if item.get("paidMonth") == current_month else current_month

    doc = await repo.update_item(
        item_id, user_id, sub_id, {"paidMonth": new_paid_month}
    )
    if not doc:
        raise not_found_error(OdinErrorCodes.ITEM_NOT_FOUND, "The item was not found.")
    return _item_dto(doc)
