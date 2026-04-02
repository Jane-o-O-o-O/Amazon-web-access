"""
AI client: supports Anthropic native SDK and any OpenAI-compatible endpoint.
Model provider / base URL / API key are all read from config (overridable at runtime).
"""
import json
import re
from typing import Any
import anthropic
from tenacity import retry, stop_after_attempt, wait_exponential
from app.config import settings
from app.ai.prompts import (
    PRODUCT_EXTRACTION_PROMPT,
    PRODUCT_MATCH_PROMPT,
    COMPETITOR_ANALYSIS_PROMPT,
    LISTING_GENERATION_PROMPT,
)


# ─── Client factory ──────────────────────────────────────────────────────────

def _make_anthropic_client(api_key: str | None = None, base_url: str | None = None) -> anthropic.Anthropic:
    return anthropic.Anthropic(
        api_key=api_key or settings.MODEL_API_KEY,
        base_url=base_url or settings.MODEL_BASE_URL,
    )


def _make_openai_client(api_key: str | None = None, base_url: str | None = None):
    try:
        from openai import OpenAI
    except ImportError:
        raise RuntimeError("openai package not installed. Run: pip install openai")
    return OpenAI(
        api_key=api_key or settings.MODEL_API_KEY,
        base_url=base_url or settings.MODEL_BASE_URL,
    )


def get_client(provider: str | None = None, api_key: str | None = None, base_url: str | None = None):
    """Return the appropriate LLM client based on provider setting."""
    p = provider or settings.MODEL_PROVIDER
    if p == "anthropic":
        return _make_anthropic_client(api_key, base_url)
    return _make_openai_client(api_key, base_url)


# ─── Unified completion helper ────────────────────────────────────────────────

def complete(
    prompt: str,
    max_tokens: int = 2048,
    provider: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    model: str | None = None,
) -> str:
    """
    Send a single-turn completion request.
    Works with both Anthropic native and OpenAI-compatible APIs.
    """
    p = provider or settings.MODEL_PROVIDER
    m = model or settings.MODEL_NAME

    if p == "anthropic":
        client = _make_anthropic_client(api_key, base_url)
        message = client.messages.create(
            model=m,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text

    else:
        client = _make_openai_client(api_key, base_url)
        response = client.chat.completions.create(
            model=m,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content


def complete_with_tools(
    prompt: str,
    tools: list[dict],
    max_tokens: int = 4096,
    provider: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    model: str | None = None,
) -> str:
    """
    Send a request with tool use (web_search etc.).
    Only Anthropic provider supports native web_search tool.
    Falls back to plain complete() for other providers.
    """
    p = provider or settings.MODEL_PROVIDER
    m = model or settings.MODEL_NAME

    if p == "anthropic":
        client = _make_anthropic_client(api_key, base_url)
        message = client.messages.create(
            model=m,
            max_tokens=max_tokens,
            tools=tools,
            messages=[{"role": "user", "content": prompt}],
        )
        parts = [block.text for block in message.content if hasattr(block, "text")]
        return "\n".join(parts)

    else:
        # OpenAI-compat: no native web_search — just run as plain chat
        return complete(prompt, max_tokens, p, api_key, base_url, m)


# ─── JSON extraction helper ───────────────────────────────────────────────────

def _extract_json(text: str) -> dict:
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        raise ValueError(f"No JSON found in LLM response: {text[:300]}")
    return json.loads(match.group())


# ─── Task-specific wrappers ───────────────────────────────────────────────────

WEB_SEARCH_TOOL = [{"type": "web_search_20250305", "name": "web_search", "max_uses": 1}]


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def extract_product_info(platform: str, content: str) -> dict:
    prompt = PRODUCT_EXTRACTION_PROMPT.format(platform=platform, content=content[:8000])
    return _extract_json(complete(prompt, max_tokens=2048))


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def match_products(source: dict, target: dict) -> dict:
    prompt = PRODUCT_MATCH_PROMPT.format(
        source=json.dumps(source, ensure_ascii=False, indent=2),
        target=json.dumps(target, ensure_ascii=False, indent=2),
    )
    return _extract_json(complete(prompt, max_tokens=1024))


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def analyze_competitors(competitors: list[dict]) -> dict:
    prompt = COMPETITOR_ANALYSIS_PROMPT.format(
        competitors=json.dumps(competitors, ensure_ascii=False, indent=2)
    )
    return _extract_json(complete(prompt, max_tokens=2048))


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def generate_listing(
    product_specs: dict,
    competitor_insights: dict,
    market: str = "amazon-us",
    keywords: list[str] | None = None,
    complaints: list[str] | None = None,
) -> dict:
    prompt = LISTING_GENERATION_PROMPT.format(
        product_specs=json.dumps(product_specs, ensure_ascii=False, indent=2),
        competitor_insights=json.dumps(competitor_insights, ensure_ascii=False, indent=2),
        market=market,
        keywords=", ".join(keywords or []),
        complaints=", ".join(complaints or []),
    )
    return _extract_json(complete(prompt, max_tokens=4096))


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def fetch_page_with_web_access(url: str) -> str:
    """Use Claude web_search tool to fetch a product page."""
    prompt = (
        f"Please fetch the content of this product page and return ALL visible text "
        f"including title, price, specs, description, and any attributes. URL: {url}"
    )
    return complete_with_tools(prompt, WEB_SEARCH_TOOL, max_tokens=4096)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def search_amazon_products(keyword: str, marketplace: str = "amazon.com") -> str:
    """Use Claude web_search tool to search Amazon for candidates."""
    search_url = f"https://www.{marketplace}/s?k={keyword.replace(' ', '+')}"
    prompt = (
        f"Search for '{keyword}' on Amazon and list the top 10 products found. "
        f"For each product include: title, price, rating, review count, ASIN (from URL), and URL. "
        f"Return as a JSON array. Search URL: {search_url}"
    )
    return complete_with_tools(prompt, WEB_SEARCH_TOOL, max_tokens=4096)
