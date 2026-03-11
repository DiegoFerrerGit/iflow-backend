from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_serializer, model_validator


# ---------------------------------------------------------------------------
# Shared
# ---------------------------------------------------------------------------

class OkResponse(BaseModel):
    ok: bool = True


class AmountWithCurrency(BaseModel):
    amount: float
    currency: Literal["USD", "ARS"]


# ---------------------------------------------------------------------------
# Pool summary
# ---------------------------------------------------------------------------

class PoolSummary(BaseModel):
    total_amount_in_usd: float
    assigned_amount_in_usd: float
    unassigned_amount_in_usd: float


# ---------------------------------------------------------------------------
# Income sources
# ---------------------------------------------------------------------------

class IncomeSourceCreate(BaseModel):
    name: str
    role: str
    effort_percentage: float = Field(ge=0, le=100)
    icon: str | None = None
    color: str
    category: str
    amount_with_currency: AmountWithCurrency


class IncomeSourceUpdate(BaseModel):
    name: str
    role: str
    effort_percentage: float = Field(ge=0, le=100)
    icon: str | None = None
    color: str
    category: str
    amount_with_currency: AmountWithCurrency


class IncomeSourceDto(BaseModel):
    id: str
    name: str
    role: str
    effort_percentage: float
    icon: str | None = None
    color: str
    category: str
    amount_with_currency: AmountWithCurrency


# ---------------------------------------------------------------------------
# Allocation boxes
# ---------------------------------------------------------------------------

class AllocationBoxCreate(BaseModel):
    name: str
    description: str
    type: Literal["permanent", "temporary"]
    calculation_type: Literal["percentage", "absolute"]
    percentage_of_pool: float | None = Field(default=None, gt=0, le=100)
    saved_amount: AmountWithCurrency | None = None
    savings_target: AmountWithCurrency | None = None
    icon: str
    color: str

    model_config = {"extra": "forbid"}

    @model_validator(mode="after")
    def _validate_by_type(self) -> "AllocationBoxCreate":
        calc = self.calculation_type
        box_type = self.type

        if calc == "percentage":
            if self.percentage_of_pool is None:
                raise ValueError(
                    f"{box_type} percentage allocation boxes require "
                    "percentage_of_pool"
                )
        elif calc == "absolute":
            if self.percentage_of_pool is not None:
                raise ValueError(
                    f"{box_type} absolute allocation boxes must not include "
                    "percentage_of_pool"
                )

        if box_type == "permanent":
            forbidden = []
            if self.saved_amount is not None:
                forbidden.append("saved_amount")
            if self.savings_target is not None:
                forbidden.append("savings_target")
            if forbidden:
                raise ValueError(
                    f"permanent {calc} allocation boxes must not include "
                    + ", ".join(forbidden)
                )
        elif box_type == "temporary":
            if self.saved_amount is not None and self.saved_amount.amount < 0:
                raise ValueError("saved_amount.amount must be >= 0")
            if (
                self.savings_target is not None
                and self.savings_target.amount <= 0
            ):
                raise ValueError("savings_target.amount must be > 0")

        return self


class AllocationBoxUpdate(AllocationBoxCreate):
    pass


class AllocationBoxDto(BaseModel):
    id: str
    name: str
    description: str
    type: Literal["permanent", "temporary"]
    calculation_type: Literal["percentage", "absolute"]
    percentage_of_pool: float | None = None
    saved_amount: AmountWithCurrency | None = None
    savings_target: AmountWithCurrency | None = None
    icon: str
    color: str
    calculated_amount_in_usd: float

    @model_serializer(mode="wrap")
    def _exclude_none(self, handler):
        return {k: v for k, v in handler(self).items() if v is not None}


# ---------------------------------------------------------------------------
# Subcategories
# ---------------------------------------------------------------------------

class SubCategoryCreate(BaseModel):
    name: str
    type: Literal["fixed_amount", "sum_items"]
    fixed_amount: float | None = Field(default=None, gt=0)
    fixed_currency: Literal["USD", "ARS"] | None = None
    icon: str | None = None
    color: str | None = None

    model_config = {"extra": "forbid"}

    @model_validator(mode="after")
    def _check_type_fields(self):
        if self.type == "fixed_amount":
            if self.fixed_amount is None or self.fixed_currency is None:
                raise ValueError(
                    "fixed_amount and fixed_currency are required for fixed_amount type"
                )
        if self.type == "sum_items":
            if self.fixed_amount is not None or self.fixed_currency is not None:
                raise ValueError(
                    "fixed_amount/fixed_currency must not be set for sum_items type"
                )
        return self


class SubCategoryUpdate(SubCategoryCreate):
    pass


class AllocationSubCategoryDto(BaseModel):
    id: str
    allocation_box_id: str
    name: str
    type: Literal["fixed_amount", "sum_items"]
    icon: str | None = None
    color: str | None = None
    display_amount: AmountWithCurrency


# ---------------------------------------------------------------------------
# Items
# ---------------------------------------------------------------------------

class ItemCreate(BaseModel):
    name: str
    description: str | None = None
    icon: str | None = None
    color: str | None = None
    amount_with_currency: AmountWithCurrency
    has_payment_control: bool = False

    model_config = {"extra": "forbid"}

    @model_validator(mode="after")
    def _check_amount(self):
        if self.amount_with_currency.amount <= 0:
            raise ValueError("Item amount must be greater than 0")
        return self


class ItemUpdate(ItemCreate):
    pass


class AllocationItemDto(BaseModel):
    id: str
    sub_category_id: str
    name: str
    description: str | None = None
    icon: str | None = None
    color: str | None = None
    amount_with_currency: AmountWithCurrency
    has_payment_control: bool
    paid: bool | None = None

    @model_serializer(mode="wrap")
    def _exclude_none(self, handler):
        return {k: v for k, v in handler(self).items() if v is not None}


# ---------------------------------------------------------------------------
# Page responses
# ---------------------------------------------------------------------------

class OdinOverviewResponse(BaseModel):
    pool_summary: PoolSummary
    income_sources: list[IncomeSourceDto]
    allocation_boxes: list[AllocationBoxDto]
    odin_onboarding: bool


class OnboardingCompletedResponse(BaseModel):
    success: bool = True


class AllocationBoxDetailResponse(BaseModel):
    available_amount_to_assign: float
    sub_categories: list[AllocationSubCategoryDto]


class SubCategoryDetailResponse(BaseModel):
    available_amount_to_assign: float
    items: list[AllocationItemDto]
