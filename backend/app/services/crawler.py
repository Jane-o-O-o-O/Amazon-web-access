"""
Crawler service — thin adapter over the web_access module.

All actual fetching logic lives in app/web_access/.
This module provides the interface that services/ and agent/tools.py use.
"""
from app.web_access.fetcher import (
    fetch_page as _fetch_page,
    fetch_pages_parallel as _fetch_parallel,
    search_amazon as _search_amazon,
    search_web as _search_web,
    detect_platform,
)


async def crawl_product_page(url: str) -> tuple[str, str]:
    """
    Fetch a product page using the best available tool.
    Returns (platform, text_content).
    """
    platform, content, _tool = await _fetch_page(url)
    return platform, content


async def crawl_pages_parallel(urls: list[str]) -> list[dict]:
    """
    Fetch multiple pages concurrently.
    Returns list of { url, platform, content, tool_used, success, error }.
    """
    return await _fetch_parallel(urls)


async def search_amazon_candidates(
    keyword: str,
    marketplace: str = "amazon.com",
) -> list[dict]:
    """
    Search Amazon and return structured candidate list.
    """
    return await _search_amazon(keyword, marketplace)


async def search_web(query: str) -> str:
    """General web search."""
    return await _search_web(query)
