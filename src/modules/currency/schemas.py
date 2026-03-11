from __future__ import annotations

from pydantic import BaseModel


class CurrencyResponse(BaseModel):
    value: float
    currency: str = "ARS"
    reference_currency: str = "USD"
    source: str = "dolarapi"
    updated_at: str
