"""
Crawler service: fetch product pages using Claude web-access.
Falls back to httpx for simple static pages.
"""
import re
import httpx
from bs4 import BeautifulSoup
from app.ai.client import fetch_page_with_web_access
from app.config import settings


def detect_platform(url: str) -> str:
    if "1688.com" in url:
        return "1688"
    if "alibaba.com" in url:
        return "alibaba"
    if "amazon.com" in url or "amazon." in url:
        return "amazon"
    return "unknown"


async def crawl_product_page(url: str) -> tuple[str, str]:
    """
    Fetch a product page and return (platform, text_content).
    Uses web-access (Claude) as primary; httpx as fallback for static pages.
    """
    platform = detect_platform(url)
    try:
        content = fetch_page_with_web_access(url)
        return platform, content
    except Exception:
        # Fallback: plain httpx for static pages
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            }
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")
            text = soup.get_text(separator="\n", strip=True)
            return platform, text


async def search_amazon_candidates(keyword: str, marketplace: str = "amazon.com") -> list[dict]:
    """
    Search Amazon for candidate products matching a keyword.
    Returns a list of candidate dicts.
    """
    from app.ai.client import search_amazon_products, _extract_json
    import json

    raw_text = search_amazon_products(keyword, marketplace)
    # Try to parse JSON array from the response
    match = re.search(r"\[[\s\S]*\]", raw_text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    # Return empty if parsing failed
    return []
