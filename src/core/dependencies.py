from __future__ import annotations

import jwt as pyjwt
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.core.errors import AuthErrorCodes, auth_error
from src.core.security.cookies import ACCESS_COOKIE_NAME
from src.core.security.jwt import verify_access_token

_bearer = HTTPBearer(auto_error=False)


async def get_current_user_id(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> str:
    token: str | None = None

    access_cookie = request.cookies.get(ACCESS_COOKIE_NAME)
    if access_cookie:
        token = access_cookie
    elif credentials:
        token = credentials.credentials

    if not token:
        raise auth_error(AuthErrorCodes.MISSING_ACCESS_TOKEN, "Missing access token.")

    try:
        payload = verify_access_token(token)
        return payload["sub"]
    except pyjwt.InvalidTokenError:
        raise auth_error(
            AuthErrorCodes.INVALID_ACCESS_TOKEN,
            "Invalid or expired access token.",
        )
