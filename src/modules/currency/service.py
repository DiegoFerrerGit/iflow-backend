"""Currency service: fetches dolar blue, caches by time window, returns latest rate."""

from __future__ import annotations

import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from src.core.config import settings
from src.core.errors import ExternalErrorCodes, external_error
from src.modules.currency.cache import get_cached, set_cached, should_refresh
from src.modules.currency.client import fetch_dolar_blue
from src.modules.currency.schemas import CurrencyResponse
from src.modules.currency.windows import get_window_key, now_ar

AR_TZ = ZoneInfo("America/Argentina/Buenos_Aires")
logger = logging.getLogger(__name__)


def _format_updated_at(fecha: str) -> str:
    """Normalize provider fecha to ISO format with Z."""
    try:
        dt = datetime.fromisoformat(fecha.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    except (ValueError, TypeError):
        return datetime.now(AR_TZ).strftime("%Y-%m-%dT%H:%M:%SZ")


async def get_latest_rate() -> CurrencyResponse:
    """
    Return the latest USD->ARS (dolar blue) rate.
    Refreshes from dolarapi.com when needed (time-window strategy).
    Falls back to cached value if provider fails.
    """
    if should_refresh():
        result = await fetch_dolar_blue()
        now = now_ar()
        wk = get_window_key(now)
        key_str = f"{wk.date}|{wk.window}" if wk else None

        if result is not None:
            value, fecha = result
            set_cached(value, fecha, key_str)
            return CurrencyResponse(
                value=value,
                currency="ARS",
                reference_currency="USD",
                source="dolarapi",
                updated_at=_format_updated_at(fecha),
            )

        cached = get_cached()
        if cached is not None:
            logger.warning("Provider failed, returning cached rate")
            return CurrencyResponse(
                value=cached.value,
                currency="ARS",
                reference_currency="USD",
                source="dolarapi",
                updated_at=_format_updated_at(cached.updated_at),
            )

        raise external_error(
            ExternalErrorCodes.EXCHANGE_RATE_PROVIDER_UNAVAILABLE,
            "Exchange rate provider is temporarily unavailable.",
        )

    cached = get_cached()
    if cached is None:
        raise external_error(
            ExternalErrorCodes.EXCHANGE_RATE_PROVIDER_UNAVAILABLE,
            "No cached exchange rate available.",
        )

    return CurrencyResponse(
        value=cached.value,
        currency="ARS",
        reference_currency="USD",
        source="dolarapi",
        updated_at=_format_updated_at(cached.updated_at),
    )


def get_fallback_rate() -> float:
    """Return config fallback when provider/cache unavailable (e.g. for profile)."""
    return settings.USD_TO_ARS_RATE_DEFAULT


async def get_rate_for_display() -> tuple[float, str]:
    """
    Return (rate, reference_date) for profile/display.
    Never raises: uses cached/fresh rate when available, else config fallback.
    """
    from datetime import date

    try:
        resp = await get_latest_rate()
        return (resp.value, resp.updated_at[:10])
    except Exception:
        return (get_fallback_rate(), date.today().isoformat())
