"""
Settings API — allows frontend to read/write model configuration at runtime.
Config is stored in Redis so it persists across restarts without redeploying.
"""
import redis as redis_lib
import json
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Literal
from app.config import settings

router = APIRouter(prefix="/api/settings", tags=["settings"])
r = redis_lib.from_url(settings.REDIS_URL)

SETTINGS_KEY = "app:model_settings"


class ModelSettings(BaseModel):
    provider: Literal["anthropic", "openai"] = "anthropic"
    base_url: str = "https://api.anthropic.com"
    api_key: str = ""
    model_name: str = "claude-sonnet-4-6"


def get_model_settings() -> ModelSettings:
    raw = r.get(SETTINGS_KEY)
    if raw:
        return ModelSettings(**json.loads(raw))
    # Defaults from env
    return ModelSettings(
        provider=settings.MODEL_PROVIDER,
        base_url=settings.MODEL_BASE_URL,
        api_key=settings.MODEL_API_KEY,
        model_name=settings.MODEL_NAME,
    )


@router.get("/model", response_model=ModelSettings)
async def read_model_settings():
    s = get_model_settings()
    # Mask the API key for security
    masked = s.model_copy()
    if masked.api_key:
        masked.api_key = masked.api_key[:8] + "••••••••"
    return masked


@router.put("/model", response_model=dict)
async def update_model_settings(body: ModelSettings):
    r.set(SETTINGS_KEY, body.model_dump_json(), ex=0)  # no expiry
    return {"ok": True, "provider": body.provider, "model": body.model_name}


@router.get("/model/providers")
async def list_providers():
    """Return supported providers with example configs."""
    return {
        "providers": [
            {
                "id": "anthropic",
                "label": "Anthropic (Claude)",
                "base_url": "https://api.anthropic.com",
                "models": ["claude-sonnet-4-6", "claude-opus-4-6", "claude-haiku-4-5-20251001"],
            },
            {
                "id": "openai",
                "label": "OpenAI",
                "base_url": "https://api.openai.com/v1",
                "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
            },
            {
                "id": "openai",
                "label": "DeepSeek",
                "base_url": "https://api.deepseek.com/v1",
                "models": ["deepseek-chat", "deepseek-coder"],
            },
            {
                "id": "openai",
                "label": "Ollama (local)",
                "base_url": "http://localhost:11434/v1",
                "models": ["llama3", "qwen2.5", "mistral"],
            },
        ]
    }


@router.get("/cdp-status")
async def cdp_status():
    """Check if the web-access CDP proxy is running."""
    from app.services.crawler import CDPCrawler
    crawler = CDPCrawler()
    available = await crawler.is_available()
    return {"available": available, "proxy_url": settings.CDP_PROXY_URL}
