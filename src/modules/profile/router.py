from fastapi import APIRouter, Depends

from src.core.dependencies import get_current_user_id
from src.modules.profile import service
from src.modules.profile.schemas import ProfileResponse

router = APIRouter()


@router.get("/profile", response_model=ProfileResponse)
async def get_profile(
    user_id: str = Depends(get_current_user_id),
) -> ProfileResponse:
    return await service.get_profile(user_id)
