from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Literal


class Settings(BaseSettings):
    # App
    APP_NAME: str = "CrossBorder AI Copilot"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/crossborder"
    DATABASE_URL_SYNC: str = "postgresql://user:password@localhost:5432/crossborder"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── Model Configuration (freely configurable) ────────────────────────────
    # Provider: "anthropic" uses native SDK; "openai" uses openai-compat client
    MODEL_PROVIDER: Literal["anthropic", "openai"] = "anthropic"
    # Base URL — override for any OpenAI-compatible endpoint
    # e.g. "https://api.openai.com/v1" / "https://api.deepseek.com/v1" / local Ollama
    MODEL_BASE_URL: str = "https://api.anthropic.com"
    MODEL_API_KEY: str = ""
    MODEL_NAME: str = "claude-sonnet-4-6"

    # ── web-access CDP proxy ─────────────────────────────────────────────────
    CDP_PROXY_URL: str = "http://localhost:3456"
    CDP_ENABLED: bool = True  # set False to skip CDP and go straight to web_search

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # CORS
    FRONTEND_URL: str = "http://localhost:3000"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
