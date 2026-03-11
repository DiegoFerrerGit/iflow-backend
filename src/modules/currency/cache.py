"""In-memory cache for currency value with time-window refresh logic."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from src.modules.currency.windows import AR_TZ, get_window_key, now_ar


@dataclass
class CachedRate:
    value: float
    updated_at: str  # ISO format from provider
    refreshed_at: str  # When we stored it (ISO)


_cache: CachedRate | None = None
_last_refresh_key: str | None = None  # "date|window" for deduplication


def get_cached() -> CachedRate | None:
    return _cache


def set_cached(value: float, updated_at: str, window_key: str | None) -> None:
    global _cache, _last_refresh_key
    _cache = CachedRate(
        value=value,
        updated_at=updated_at,
        refreshed_at=datetime.now(AR_TZ).isoformat(),
    )
    _last_refresh_key = window_key


def should_refresh() -> bool:
    """
    True if we need to fetch from the provider.
    - No cache: always refresh
    - Has cache, inside window: refresh if we haven't refreshed in this window today
    - Has cache, outside window: no refresh (use stale)
    """
    global _last_refresh_key

    cached = _cache
    now = now_ar()
    wk = get_window_key(now)

    if cached is None:
        return True

    if wk is None:
        return False

    current_key = f"{wk.date}|{wk.window}"
    if _last_refresh_key == current_key:
        return False

    return True
