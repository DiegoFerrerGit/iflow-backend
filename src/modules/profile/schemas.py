from __future__ import annotations

from pydantic import BaseModel


class UserOut(BaseModel):
    id: str
    email: str
    full_name: str | None = None
    avatar_url: str | None = None


class PreferencesOut(BaseModel):
    display_currency: str = "USD"


class ExchangeRateOut(BaseModel):
    reference_date: str
    usd_to_ars_rate: float


class ProfileResponse(BaseModel):
    user: UserOut
    preferences: PreferencesOut
    exchange_rate: ExchangeRateOut
