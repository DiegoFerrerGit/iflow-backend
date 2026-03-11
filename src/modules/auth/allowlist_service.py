import hmac
import logging

from src.core.config import settings
from src.core.errors import (
    AuthErrorCodes,
    CommonErrorCodes,
    auth_error,
    business_error,
    permission_error,
)
from src.modules.auth import allowlist_repository as repo

logger = logging.getLogger(__name__)


def _normalize_email(email: str) -> str:
    return email.strip().lower()


async def signup(email: str, signup_secret: str) -> None:
    if not settings.ALLOWLIST_ENABLED:
        raise business_error(
            CommonErrorCodes.ALLOWLIST_DISABLED,
            "Allowlist is disabled.",
        )

    if not hmac.compare_digest(signup_secret, settings.BETA_SIGNUP_SECRET):
        raise permission_error(
            AuthErrorCodes.INVALID_SIGNUP_SECRET,
            "Invalid signup secret.",
        )

    normalized = _normalize_email(email)
    await repo.upsert_allowed_email(normalized)
    logger.info("Email '%s' added to allowlist", normalized)


async def enforce_allowlist(email: str) -> None:
    if not settings.ALLOWLIST_ENABLED:
        return

    normalized = _normalize_email(email)
    if not await repo.is_email_allowed(normalized):
        logger.warning("Login denied for non-allowed email '%s'", normalized)
        raise auth_error(
            AuthErrorCodes.EMAIL_NOT_ALLOWED,
            "This email is not enabled for IFLOW yet.",
        )
