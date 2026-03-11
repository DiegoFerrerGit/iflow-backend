from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from fastapi import Response
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from src.core.config import settings
from src.core.errors import AuthErrorCodes, ExternalErrorCodes, auth_error, external_error
from src.core.security.cookies import (
    clear_access_cookie,
    clear_refresh_cookie,
    set_access_cookie,
    set_refresh_cookie,
)
from src.core.security.hashing import hash_token
from src.core.security.jwt import create_access_token
from src.core.security.refresh_tokens import generate_refresh_token
from src.modules.auth import repository as repo

logger = logging.getLogger(__name__)


async def _verify_google_token(token: str) -> dict:
    try:
        return await asyncio.to_thread(
            id_token.verify_oauth2_token,
            token,
            google_requests.Request(),
            settings.GOOGLE_OAUTH_CLIENT_ID,
        )
    except ValueError as exc:
        logger.warning("Google token verification failed: %s", exc)
        raise external_error(
            ExternalErrorCodes.INVALID_GOOGLE_TOKEN,
            f"Invalid Google token: {exc}",
        )


async def google_login(id_token_str: str, response: Response) -> None:
    google_info = await _verify_google_token(id_token_str)

    from src.modules.auth.allowlist_service import enforce_allowlist

    await enforce_allowlist(google_info["email"])

    user = await repo.upsert_user(
        google_sub=google_info["sub"],
        email=google_info["email"],
        full_name=google_info.get("name"),
        avatar_url=google_info.get("picture"),
    )

    refresh_token = generate_refresh_token()
    expires_at = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_TTL_DAYS,
    )
    await repo.create_session(
        user_id=user["_id"],
        refresh_token_hash=hash_token(refresh_token),
        expires_at=expires_at,
    )

    access_token = create_access_token(str(user["_id"]), user["email"])

    set_access_cookie(response, access_token)
    set_refresh_cookie(response, refresh_token)

    logger.info("User '%s' logged in via Google", user["email"])


async def refresh_tokens(raw_token: str | None, response: Response) -> None:
    if not raw_token:
        raise auth_error(AuthErrorCodes.MISSING_REFRESH_TOKEN, "Missing refresh token.")

    session = await repo.find_valid_session(hash_token(raw_token))
    if not session:
        raise auth_error(AuthErrorCodes.INVALID_SESSION, "Invalid or expired session.")

    user = await repo.find_user_by_id(str(session["userId"]))
    if not user:
        raise auth_error(AuthErrorCodes.USER_NOT_FOUND, "User not found.")

    new_refresh = generate_refresh_token()
    new_expires = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_TTL_DAYS,
    )
    await repo.rotate_session(session["_id"], hash_token(new_refresh), new_expires)

    access_token = create_access_token(str(user["_id"]), user["email"])

    set_access_cookie(response, access_token)
    set_refresh_cookie(response, new_refresh)

    logger.info("Tokens refreshed for user '%s'", user["email"])


async def logout(raw_token: str | None, response: Response) -> None:
    if raw_token:
        await repo.revoke_session(hash_token(raw_token))
    clear_access_cookie(response)
    clear_refresh_cookie(response)
    logger.info("User logged out")
