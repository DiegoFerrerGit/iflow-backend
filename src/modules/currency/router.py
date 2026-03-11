from fastapi import APIRouter, Depends

from src.core.dependencies import get_current_user_id
from src.modules.currency.schemas import CurrencyResponse
from src.modules.currency import service

router = APIRouter()


@router.get("/currency", response_model=CurrencyResponse)
async def get_currency(
    _user_id: str = Depends(get_current_user_id),
) -> CurrencyResponse:
    """Return the latest USD->ARS (dolar blue) rate. Requires authentication."""
    return await service.get_latest_rate()
