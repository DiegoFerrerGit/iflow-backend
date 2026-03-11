import logging
from datetime import datetime, timedelta, timezone

import jwt as pyjwt

from src.core.config import settings

logger = logging.getLogger(__name__)

_ALGORITHM = "HS256"


def create_access_token(user_id: str, email: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "email": email,
        "iat": now,
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_TTL_MIN),
        "type": "access",
    }
    return pyjwt.encode(payload, settings.JWT_ACCESS_SECRET, algorithm=_ALGORITHM)


def verify_access_token(token: str) -> dict:
    try:
        payload = pyjwt.decode(
            token,
            settings.JWT_ACCESS_SECRET,
            algorithms=[_ALGORITHM],
        )
        if payload.get("type") != "access":
            raise pyjwt.InvalidTokenError("Invalid token type")
        return payload
    except pyjwt.ExpiredSignatureError:
        logger.warning("Access token expired")
        raise
    except pyjwt.InvalidTokenError:
        logger.warning("Invalid access token")
        raise
