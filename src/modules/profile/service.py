from src.core.errors import AuthErrorCodes, not_found_error
from src.modules.currency import service as currency_service
from src.modules.profile import repository as repo
from src.modules.profile.schemas import (
    ExchangeRateOut,
    PreferencesOut,
    ProfileResponse,
    UserOut,
)


async def get_profile(user_id: str) -> ProfileResponse:
    user = await repo.find_user_by_id(user_id)
    if not user:
        raise not_found_error(AuthErrorCodes.USER_NOT_FOUND, "User not found.")

    prefs = user.get("preferences", {})

    rate, reference_date = await currency_service.get_rate_for_display()

    return ProfileResponse(
        user=UserOut(
            id=str(user["_id"]),
            email=user["email"],
            full_name=user.get("fullName"),
            avatar_url=user.get("avatarUrl"),
        ),
        preferences=PreferencesOut(
            display_currency=prefs.get("displayCurrency", "USD"),
        ),
        exchange_rate=ExchangeRateOut(
            reference_date=reference_date,
            usd_to_ars_rate=rate,
        ),
    )
