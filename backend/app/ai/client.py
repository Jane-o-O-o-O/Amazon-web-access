import json
import re
import anthropic
from tenacity import retry, stop_after_attempt, wait_exponential
from app.config import settings
from app.ai.prompts import (
    PRODUCT_EXTRACTION_PROMPT,
    PRODUCT_MATCH_PROMPT,
    COMPETITOR_ANALYSIS_PROMPT,
    LISTING_GENERATION_PROMPT,
)

client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)


def _extract_json(text: str) -> dict:
    """Extract the first JSON object from a string."""
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        raise ValueError(f"No JSON found in response: {text[:200]}")
    return json.loads(match.group())


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def extract_product_info(platform: str, content: str) -> dict:
    """Use Claude to extract structured product info from raw page content."""
    prompt = PRODUCT_EXTRACTION_PROMPT.format(platform=platform, content=content[:8000])
    message = client.messages.create(
        model=settings.CLAUDE_MODEL,
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    return _extract_json(message.content[0].text)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def match_products(source: dict, target: dict) -> dict:
    """Use Claude to score similarity between two products."""
    prompt = PRODUCT_MATCH_PROMPT.format(
        source=json.dumps(source, ensure_ascii=False, indent=2),
        target=json.dumps(target, ensure_ascii=False, indent=2),
    )
    message = client.messages.create(
        model=settings.CLAUDE_MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return _extract_json(message.content[0].text)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def analyze_competitors(competitors: list[dict]) -> dict:
    """Use Claude to generate a competitor analysis report."""
    prompt = COMPETITOR_ANALYSIS_PROMPT.format(
        competitors=json.dumps(competitors, ensure_ascii=False, indent=2)
    )
    message = client.messages.create(
        model=settings.CLAUDE_MODEL,
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    return _extract_json(message.content[0].text)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def generate_listing(
    product_specs: dict,
    competitor_insights: dict,
    market: str = "amazon-us",
    keywords: list[str] | None = None,
    complaints: list[str] | None = None,
) -> dict:
    """Use Claude to generate a full Amazon listing."""
    prompt = LISTING_GENERATION_PROMPT.format(
        product_specs=json.dumps(product_specs, ensure_ascii=False, indent=2),
        competitor_insights=json.dumps(competitor_insights, ensure_ascii=False, indent=2),
        market=market,
        keywords=", ".join(keywords or []),
        complaints=", ".join(complaints or []),
    )
    message = client.messages.create(
        model=settings.CLAUDE_MODEL,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    return _extract_json(message.content[0].text)


def fetch_page_with_web_access(url: str) -> str:
    """
    Use Claude's web_search / web_fetch tool (web-access) to retrieve a webpage.
    Returns the text content of the page.
    """
    message = client.messages.create(
        model=settings.CLAUDE_MODEL,
        max_tokens=4096,
        tools=[
            {
                "type": "web_search_20250305",
                "name": "web_search",
                "max_uses": 1,
            }
        ],
        messages=[
            {
                "role": "user",
                "content": (
                    f"Please fetch the content of this product page and return ALL visible text "
                    f"including title, price, specs, description, and any attributes. URL: {url}"
                ),
            }
        ],
    )
    # Collect all text from the response
    parts = []
    for block in message.content:
        if hasattr(block, "text"):
            parts.append(block.text)
    return "\n".join(parts)


def search_amazon_products(keyword: str, marketplace: str = "amazon.com") -> str:
    """
    Search Amazon for products using web-access.
    Returns raw text of search results page.
    """
    search_url = f"https://www.{marketplace}/s?k={keyword.replace(' ', '+')}"
    message = client.messages.create(
        model=settings.CLAUDE_MODEL,
        max_tokens=4096,
        tools=[
            {
                "type": "web_search_20250305",
                "name": "web_search",
                "max_uses": 1,
            }
        ],
        messages=[
            {
                "role": "user",
                "content": (
                    f"Search for '{keyword}' on Amazon and list the top 10 products found. "
                    f"For each product include: title, price, rating, review count, ASIN (from URL), and URL. "
                    f"Return as a JSON array. Search URL: {search_url}"
                ),
            }
        ],
    )
    parts = []
    for block in message.content:
        if hasattr(block, "text"):
            parts.append(block.text)
    return "\n".join(parts)
