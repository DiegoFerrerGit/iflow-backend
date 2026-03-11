"""Parser for dolarapi.com response. Extracts dolar blue (venta) only."""

from __future__ import annotations

DOLLAR_BLUE_CASA = "blue"


def parse_dolar_blue(raw: list[dict]) -> tuple[float, str] | None:
    """
    Parse dolarapi.com response and extract dolar blue value.
    Returns (value, fecha_actualizacion) or None if not found/invalid.
    """
    if not raw or not isinstance(raw, list):
        return None

    for item in raw:
        if not isinstance(item, dict):
            continue
        if item.get("casa") == DOLLAR_BLUE_CASA:
            venta = item.get("venta")
            fecha = item.get("fechaActualizacion", "")
            if venta is not None:
                try:
                    value = float(venta)
                    if value > 0:
                        return (value, str(fecha))
                except (TypeError, ValueError):
                    pass
            return None

    return None
