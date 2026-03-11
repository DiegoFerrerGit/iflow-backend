"""Argentina business hours time windows for currency refresh."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time
from zoneinfo import ZoneInfo

AR_TZ = ZoneInfo("America/Argentina/Buenos_Aires")

# Window boundaries (inclusive start, exclusive end for simplicity)
PRE_MARKET_START = time(8, 0)
PRE_MARKET_END = time(10, 0)
MARKET_START = time(10, 0)
MARKET_END = time(16, 0)
POST_MARKET_START = time(16, 0)
POST_MARKET_END = time(18, 1)  # 18:00 inclusive


@dataclass(frozen=True)
class WindowKey:
    """Identifies a refresh window: date + window name."""

    date: str  # YYYY-MM-DD in Argentina
    window: str  # "pre_market" | "market_hours" | "post_market"


def now_ar() -> datetime:
    """Current datetime in Argentina timezone."""
    return datetime.now(AR_TZ)


def get_current_window(dt: datetime) -> str | None:
    """
    Return current window name or None if outside business hours.
    Windows: pre_market (08:00-09:59), market_hours (10:00-15:59), post_market (16:00-18:00).
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=AR_TZ)
    t = dt.astimezone(AR_TZ).time()
    if PRE_MARKET_START <= t < PRE_MARKET_END:
        return "pre_market"
    if MARKET_START <= t < MARKET_END:
        return "market_hours"
    if POST_MARKET_START <= t < POST_MARKET_END:
        return "post_market"
    return None


def get_window_key(dt: datetime) -> WindowKey | None:
    """Return WindowKey for the given datetime, or None if outside windows."""
    window = get_current_window(dt)
    if window is None:
        return None
    date_str = dt.strftime("%Y-%m-%d")
    return WindowKey(date=date_str, window=window)
