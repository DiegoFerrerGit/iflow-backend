"""HTTP client for dolarapi.com. Fetches dolar blue only."""

from __future__ import annotations

import logging

import httpx

from src.modules.currency.parser import parse_dolar_blue

logger = logging.getLogger(__name__)

DOLARAPI_URL = "https://dolarapi.com/v1/dolares"


async def fetch_dolar_blue() -> tuple[float, str] | None:
    """
    Fetch dolar blue from dolarapi.com.
    Returns (value, fecha_actualizacion) or None on failure.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(DOLARAPI_URL)
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPError as exc:
        logger.warning("Dolarapi fetch failed: %s", exc)
        return None
    except Exception as exc:
        logger.warning("Dolarapi unexpected error: %s", exc)
        return None

    result = parse_dolar_blue(data)
    if result is None:
        logger.warning("Dolarapi response missing or invalid dolar blue")
        return None

    return result
