import os

from pydantic_settings import BaseSettings

_env_file = os.getenv("ENV_FILE", ".env.local")


class Settings(BaseSettings):
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "iflow_dev"
    FRONTEND_ORIGIN: str = "http://localhost:4200"
    JWT_ACCESS_SECRET: str = "iflow_dev_access_secret_change_me_2026"
    JWT_REFRESH_SECRET: str = "iflow_dev_refresh_secret_change_me_2026"
    ACCESS_TOKEN_TTL_MIN: int = 15
    REFRESH_TOKEN_TTL_DAYS: int = 30
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: str = "lax"
    USD_TO_ARS_RATE_DEFAULT: float = 1450
    GOOGLE_OAUTH_CLIENT_ID: str = "CHANGE_ME"
    ALLOWLIST_ENABLED: bool = True
    BETA_SIGNUP_SECRET: str = "Xt7kQ9mZrW4vLpJ2nBcYdA8sF6hG3eUoRiDwKxMaTqNjCyVbEf5u"
    API_DELAY_SECONDS: float = 0

    model_config = {
        "env_file": _env_file,
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
