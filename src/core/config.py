"""
Configuration for iflow-api.

Loading priority (highest to lowest):
  1. Environment variables (e.g. set in Render, shell, or system)
  2. .env file (path from ENV_FILE, default: .env.local)
  3. Safe defaults (only for non-sensitive values)

Production (e.g. Render):
  Set all required variables as environment variables in the dashboard.
  Do NOT rely on .env files in production.

Local development:
  Use .env.local with required values. The file is gitignored.
  Copy from .env.example if needed.
"""

import os

from pydantic_settings import BaseSettings

_env_file = os.getenv("ENV_FILE", ".env.local")


class Settings(BaseSettings):
    # Required – no defaults. App fails to start if missing.
    MONGODB_URI: str
    MONGODB_DB_NAME: str
    JWT_ACCESS_SECRET: str
    JWT_REFRESH_SECRET: str
    GOOGLE_OAUTH_CLIENT_ID: str
    FRONTEND_ORIGIN: str

    # Optional – safe defaults
    ACCESS_TOKEN_TTL_MIN: int = 15
    REFRESH_TOKEN_TTL_DAYS: int = 30
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: str = "lax"
    USD_TO_ARS_RATE_DEFAULT: float = 1450
    API_DELAY_SECONDS: float = 0
    ALLOWLIST_ENABLED: bool = True
    BETA_SIGNUP_SECRET: str = ""  # Required for signup when ALLOWLIST_ENABLED

    # Optional – comma-separated origins for CORS (e.g. mobile dev)
    FRONTEND_ORIGINS: str | None = None

    model_config = {
        "env_file": _env_file,
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
