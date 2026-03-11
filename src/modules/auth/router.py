from __future__ import annotations

from fastapi import APIRouter, Cookie, Response

from src.core.security.cookies import REFRESH_COOKIE_NAME
from src.modules.auth import allowlist_service, service
from src.modules.auth.schemas import GoogleLoginRequest, OkResponse, SignupRequest

router = APIRouter()


@router.post("/google", response_model=OkResponse)
async def google_login(body: GoogleLoginRequest, response: Response) -> OkResponse:
    await service.google_login(body.id_token, response)
    return OkResponse()


@router.post("/refresh", response_model=OkResponse)
async def refresh(
    response: Response,
    refresh_token: str | None = Cookie(None, alias=REFRESH_COOKIE_NAME),
) -> OkResponse:
    await service.refresh_tokens(refresh_token, response)
    return OkResponse()


@router.post("/signup", response_model=OkResponse)
async def signup(body: SignupRequest) -> OkResponse:
    await allowlist_service.signup(body.email, body.signup_secret)
    return OkResponse()


@router.post("/logout", response_model=OkResponse)
async def logout(
    response: Response,
    refresh_token: str | None = Cookie(None, alias=REFRESH_COOKIE_NAME),
) -> OkResponse:
    await service.logout(refresh_token, response)
    return OkResponse()
