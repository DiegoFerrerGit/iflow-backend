from fastapi import APIRouter, Body, Depends

from src.core.dependencies import get_current_user_id
from src.modules.odin import service
from src.modules.odin.schemas import (
    AllocationBoxCreate,
    AllocationBoxDetailResponse,
    AllocationBoxDto,
    AllocationBoxUpdate,
    AllocationItemDto,
    AllocationSubCategoryDto,
    IncomeSourceCreate,
    IncomeSourceDto,
    IncomeSourceUpdate,
    ItemCreate,
    ItemUpdate,
    OdinOverviewResponse,
    OkResponse,
    OnboardingCompletedResponse,
    SubCategoryCreate,
    SubCategoryDetailResponse,
    SubCategoryUpdate,
)

router = APIRouter()

_BOX_EXAMPLES = {
    "permanent_percentage": {
        "summary": "Permanent percentage allocation box",
        "description": "Allocates a percentage of the total income pool.",
        "value": {
            "name": "Inversión",
            "description": "Patrimonio & Capital",
            "type": "permanent",
            "calculation_type": "percentage",
            "percentage_of_pool": 35,
            "icon": "trending_up",
            "color": "emerald",
        },
    },
    "permanent_absolute": {
        "summary": "Permanent absolute allocation box",
        "description": (
            "No amount is set at creation. The calculated value is "
            "derived from its subcategories and items."
        ),
        "value": {
            "name": "Calidad de Vida",
            "description": "Gastos Fijos Esenciales",
            "type": "permanent",
            "calculation_type": "absolute",
            "icon": "home",
            "color": "crimson",
        },
    },
    "temporary_percentage": {
        "summary": "Temporary percentage allocation box",
        "description": (
            "Goal-based savings box whose budget comes from a pool "
            "percentage, with optional progress tracking."
        ),
        "value": {
            "name": "Emergencia",
            "description": "Blindaje (3-6 meses Fijos)",
            "type": "temporary",
            "calculation_type": "percentage",
            "percentage_of_pool": 10,
            "saved_amount": {"amount": 3900, "currency": "USD"},
            "savings_target": {"amount": 12000, "currency": "USD"},
            "icon": "security",
            "color": "gold",
        },
    },
    "temporary_absolute": {
        "summary": "Temporary absolute allocation box",
        "description": (
            "Goal-based savings box whose value is derived from its "
            "subcategories, with optional progress tracking."
        ),
        "value": {
            "name": "Emergencia",
            "description": "Blindaje (3-6 meses Fijos)",
            "type": "temporary",
            "calculation_type": "absolute",
            "saved_amount": {"amount": 3900, "currency": "USD"},
            "savings_target": {"amount": 12000, "currency": "USD"},
            "icon": "security",
            "color": "gold",
        },
    },
}

_BOX_RESPONSE_EXAMPLES = {
    "permanent_percentage": {
        "summary": "Permanent percentage allocation box",
        "value": {
            "id": "6751a2b3c4d5e6f7a8b9c0d1",
            "name": "Inversión",
            "description": "Patrimonio & Capital",
            "type": "permanent",
            "calculation_type": "percentage",
            "percentage_of_pool": 35,
            "icon": "trending_up",
            "color": "emerald",
            "calculated_amount_in_usd": 1050.0,
        },
    },
    "permanent_absolute": {
        "summary": "Permanent absolute allocation box",
        "value": {
            "id": "6751a2b3c4d5e6f7a8b9c0d2",
            "name": "Calidad de Vida",
            "description": "Gastos Fijos Esenciales",
            "type": "permanent",
            "calculation_type": "absolute",
            "icon": "home",
            "color": "crimson",
            "calculated_amount_in_usd": 0.0,
        },
    },
    "temporary_percentage": {
        "summary": "Temporary percentage allocation box",
        "value": {
            "id": "6751a2b3c4d5e6f7a8b9c0d3",
            "name": "Emergencia",
            "description": "Blindaje (3-6 meses Fijos)",
            "type": "temporary",
            "calculation_type": "percentage",
            "percentage_of_pool": 10,
            "saved_amount": {"amount": 3900, "currency": "USD"},
            "savings_target": {"amount": 12000, "currency": "USD"},
            "icon": "security",
            "color": "gold",
            "calculated_amount_in_usd": 300.0,
        },
    },
    "temporary_absolute": {
        "summary": "Temporary absolute allocation box",
        "value": {
            "id": "6751a2b3c4d5e6f7a8b9c0d4",
            "name": "Emergencia",
            "description": "Blindaje (3-6 meses Fijos)",
            "type": "temporary",
            "calculation_type": "absolute",
            "saved_amount": {"amount": 3900, "currency": "USD"},
            "savings_target": {"amount": 12000, "currency": "USD"},
            "icon": "security",
            "color": "gold",
            "calculated_amount_in_usd": 0.0,
        },
    },
}

_BOX_RESPONSES = {
    200: {
        "content": {
            "application/json": {"examples": _BOX_RESPONSE_EXAMPLES}
        },
    },
}

_BOX_RESPONSES_201 = {
    201: {
        "content": {
            "application/json": {"examples": _BOX_RESPONSE_EXAMPLES}
        },
    },
}


# ---------------------------------------------------------------------------
# Overview
# ---------------------------------------------------------------------------

@router.get("", response_model=OdinOverviewResponse)
async def get_overview(
    user_id: str = Depends(get_current_user_id),
) -> OdinOverviewResponse:
    return await service.get_overview(user_id)


@router.patch("/onboarding-completed", response_model=OnboardingCompletedResponse)
async def mark_onboarding_completed(
    user_id: str = Depends(get_current_user_id),
) -> OnboardingCompletedResponse:
    await service.mark_onboarding_completed(user_id)
    return OnboardingCompletedResponse()


# ---------------------------------------------------------------------------
# Income sources
# ---------------------------------------------------------------------------

@router.get("/income-sources", response_model=list[IncomeSourceDto])
async def list_income_sources(
    user_id: str = Depends(get_current_user_id),
) -> list[IncomeSourceDto]:
    return await service.list_income_sources(user_id)


@router.post(
    "/income-sources", response_model=IncomeSourceDto, status_code=201
)
async def create_income_source(
    body: IncomeSourceCreate,
    user_id: str = Depends(get_current_user_id),
) -> IncomeSourceDto:
    return await service.create_income_source(user_id, body)


@router.put(
    "/income-sources/{income_source_id}", response_model=IncomeSourceDto
)
async def update_income_source(
    income_source_id: str,
    body: IncomeSourceUpdate,
    user_id: str = Depends(get_current_user_id),
) -> IncomeSourceDto:
    return await service.update_income_source(user_id, income_source_id, body)


@router.delete("/income-sources/{income_source_id}", response_model=OkResponse)
async def delete_income_source(
    income_source_id: str,
    user_id: str = Depends(get_current_user_id),
) -> OkResponse:
    await service.delete_income_source(user_id, income_source_id)
    return OkResponse()


# ---------------------------------------------------------------------------
# Allocation boxes
# ---------------------------------------------------------------------------

@router.get("/allocation-boxes", response_model=list[AllocationBoxDto])
async def list_allocation_boxes(
    user_id: str = Depends(get_current_user_id),
) -> list[AllocationBoxDto]:
    return await service.list_allocation_boxes(user_id)


@router.post(
    "/allocation-boxes",
    response_model=AllocationBoxDto,
    status_code=201,
    responses=_BOX_RESPONSES_201,
)
async def create_allocation_box(
    body: AllocationBoxCreate = Body(openapi_examples=_BOX_EXAMPLES),
    user_id: str = Depends(get_current_user_id),
) -> AllocationBoxDto:
    return await service.create_allocation_box(user_id, body)


@router.put(
    "/allocation-boxes/{allocation_box_id}",
    response_model=AllocationBoxDto,
    responses=_BOX_RESPONSES,
)
async def update_allocation_box(
    allocation_box_id: str,
    body: AllocationBoxUpdate = Body(openapi_examples=_BOX_EXAMPLES),
    user_id: str = Depends(get_current_user_id),
) -> AllocationBoxDto:
    return await service.update_allocation_box(user_id, allocation_box_id, body)


@router.delete(
    "/allocation-boxes/{allocation_box_id}", response_model=OkResponse
)
async def delete_allocation_box(
    allocation_box_id: str,
    user_id: str = Depends(get_current_user_id),
) -> OkResponse:
    await service.delete_allocation_box(user_id, allocation_box_id)
    return OkResponse()


# ---------------------------------------------------------------------------
# Allocation box detail (level 2)
# ---------------------------------------------------------------------------

@router.get(
    "/allocation-boxes/{allocation_box_id}",
    response_model=AllocationBoxDetailResponse,
)
async def get_allocation_box_detail(
    allocation_box_id: str,
    user_id: str = Depends(get_current_user_id),
) -> AllocationBoxDetailResponse:
    return await service.get_box_detail(user_id, allocation_box_id)


# ---------------------------------------------------------------------------
# Subcategories
# ---------------------------------------------------------------------------

_SUB_EXAMPLES = {
    "fixed_amount": {
        "summary": "Fixed amount subcategory",
        "description": "The amount is set directly and returned as-is.",
        "value": {
            "name": "Alquiler",
            "type": "fixed_amount",
            "fixed_amount": 800,
            "fixed_currency": "USD",
            "icon": "apartment",
            "color": "crimson",
        },
    },
    "sum_items": {
        "summary": "Sum of items subcategory",
        "description": (
            "No amount is set. The display amount is calculated "
            "from its child items."
        ),
        "value": {
            "name": "Servicios",
            "type": "sum_items",
            "icon": "receipt_long",
            "color": "cyan",
        },
    },
}

@router.post(
    "/allocation-boxes/{allocation_box_id}/subcategories",
    response_model=AllocationSubCategoryDto,
    status_code=201,
)
async def create_subcategory(
    allocation_box_id: str,
    body: SubCategoryCreate = Body(openapi_examples=_SUB_EXAMPLES),
    user_id: str = Depends(get_current_user_id),
) -> AllocationSubCategoryDto:
    return await service.create_subcategory(user_id, allocation_box_id, body)


@router.put(
    "/allocation-boxes/{allocation_box_id}/subcategories/{sub_category_id}",
    response_model=AllocationSubCategoryDto,
)
async def update_subcategory(
    allocation_box_id: str,
    sub_category_id: str,
    body: SubCategoryUpdate = Body(openapi_examples=_SUB_EXAMPLES),
    user_id: str = Depends(get_current_user_id),
) -> AllocationSubCategoryDto:
    return await service.update_subcategory(
        user_id, allocation_box_id, sub_category_id, body
    )


@router.delete(
    "/allocation-boxes/{allocation_box_id}/subcategories/{sub_category_id}",
    response_model=OkResponse,
)
async def delete_subcategory(
    allocation_box_id: str,
    sub_category_id: str,
    user_id: str = Depends(get_current_user_id),
) -> OkResponse:
    await service.delete_subcategory(user_id, allocation_box_id, sub_category_id)
    return OkResponse()


# ---------------------------------------------------------------------------
# Subcategory detail (level 3)
# ---------------------------------------------------------------------------

@router.get(
    "/allocation-boxes/{allocation_box_id}/subcategories/{sub_category_id}",
    response_model=SubCategoryDetailResponse,
)
async def get_subcategory_detail(
    allocation_box_id: str,
    sub_category_id: str,
    user_id: str = Depends(get_current_user_id),
) -> SubCategoryDetailResponse:
    return await service.get_subcategory_detail(
        user_id, allocation_box_id, sub_category_id
    )


# ---------------------------------------------------------------------------
# Items
# ---------------------------------------------------------------------------

_ITEM_EXAMPLES = {
    "with_payment_control": {
        "summary": "Item with payment control",
        "description": "Monthly trackable payment. Shows paid/pending toggle.",
        "value": {
            "name": "Internet",
            "description": "Fibra óptica 300 Mbps",
            "icon": "wifi",
            "color": "cyan",
            "amount_with_currency": {"amount": 45, "currency": "USD"},
            "has_payment_control": True,
        },
    },
    "without_payment_control": {
        "summary": "Item without payment control",
        "description": "Simple allocation item. No paid/pending tracking.",
        "value": {
            "name": "Ahorro mensual",
            "description": "Aporte fijo al fondo",
            "icon": "savings",
            "color": "emerald",
            "amount_with_currency": {"amount": 200, "currency": "USD"},
            "has_payment_control": False,
        },
    },
}

@router.post(
    "/allocation-boxes/{allocation_box_id}/subcategories/{sub_category_id}/items",
    response_model=AllocationItemDto,
    status_code=201,
)
async def create_item(
    allocation_box_id: str,
    sub_category_id: str,
    body: ItemCreate = Body(openapi_examples=_ITEM_EXAMPLES),
    user_id: str = Depends(get_current_user_id),
) -> AllocationItemDto:
    return await service.create_item(
        user_id, allocation_box_id, sub_category_id, body
    )


@router.put(
    "/allocation-boxes/{allocation_box_id}/subcategories/{sub_category_id}/items/{item_id}",
    response_model=AllocationItemDto,
)
async def update_item(
    allocation_box_id: str,
    sub_category_id: str,
    item_id: str,
    body: ItemUpdate = Body(openapi_examples=_ITEM_EXAMPLES),
    user_id: str = Depends(get_current_user_id),
) -> AllocationItemDto:
    return await service.update_item(
        user_id, allocation_box_id, sub_category_id, item_id, body
    )


@router.delete(
    "/allocation-boxes/{allocation_box_id}/subcategories/{sub_category_id}/items/{item_id}",
    response_model=OkResponse,
)
async def delete_item(
    allocation_box_id: str,
    sub_category_id: str,
    item_id: str,
    user_id: str = Depends(get_current_user_id),
) -> OkResponse:
    await service.delete_item(
        user_id, allocation_box_id, sub_category_id, item_id
    )
    return OkResponse()


@router.patch(
    "/allocation-boxes/{allocation_box_id}/subcategories/{sub_category_id}/items/{item_id}/toggle-paid",
    response_model=AllocationItemDto,
)
async def toggle_item_paid(
    allocation_box_id: str,
    sub_category_id: str,
    item_id: str,
    user_id: str = Depends(get_current_user_id),
) -> AllocationItemDto:
    return await service.toggle_item_paid(
        user_id, allocation_box_id, sub_category_id, item_id
    )
