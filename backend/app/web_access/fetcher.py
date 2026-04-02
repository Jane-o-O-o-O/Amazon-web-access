"""
Main public API for the web_access module.

This is what the rest of the app imports and uses.
It orchestrates CDP client, strategy selection, and site experience.

Public functions:
  fetch_page(url)          → (platform, content, tool_used)
  fetch_pages_parallel(urls) → list of results, concurrent
  search_amazon(keyword)   → list[dict] candidates
  search_web(query)        → str summary
"""
import asyncio
import re
import json
from typing import Literal

from app.web_access.cdp_client import CDPClient, ManagedTab
from app.web_access.strategy import (
    ToolChoice, decide_tool,
    fetch_via_jina, fetch_via_curl,
    fetch_via_web_fetch, search_via_web_search,
)
from app.web_access.site_experience import (
    get_site_experience, record_success, record_failure,
    get_wait_time, needs_scroll, get_selectors,
)

# Shared CDP client instance (reused across requests)
_cdp = CDPClient()


# ── Platform detection ─────────────────────────────────────────────────────────

def detect_platform(url: str) -> str:
    u = url.lower()
    if "1688.com" in u:   return "1688"
    if "alibaba.com" in u: return "alibaba"
    if "amazon." in u:     return "amazon"
    if "taobao.com" in u:  return "taobao"
    if "shopify" in u or "myshopify" in u: return "shopify"
    return "unknown"


# ── CDP fetch (full flow with site-aware behavior) ─────────────────────────────

async def _fetch_via_cdp(url: str, platform: str) -> str:
    """
    Full CDP fetch:
    1. Open tab
    2. Wait for JS render (site-specific duration)
    3. Scroll if needed (triggers lazy loading)
    4. Try structured DOM extraction (platform-aware selectors)
    5. Fallback to full innerText
    6. Close tab
    """
    wait = get_wait_time(url)
    scroll = needs_scroll(url)

    async with ManagedTab(_cdp, url) as tab_id:
        await asyncio.sleep(wait)

        if scroll:
            await _cdp.scroll(tab_id, "down")
            await asyncio.sleep(0.8)
            await _cdp.scroll(tab_id, "down")  # twice for full lazy load
            await asyncio.sleep(0.5)

        # Try platform-aware structured extraction
        structured = await _cdp.extract_product_data(tab_id, platform)
        raw_text = structured.pop("_raw_text", "") or ""

        # Combine structured + raw text for richest output
        parts = []
        for k, v in structured.items():
            if v:
                if isinstance(v, (list, dict)):
                    parts.append(f"{k}: {json.dumps(v, ensure_ascii=False)}")
                else:
                    parts.append(f"{k}: {v}")
        if raw_text:
            parts.append(raw_text)

        content = "\n".join(parts)
        return content if len(content.strip()) > 100 else raw_text


# ── Main fetch function ────────────────────────────────────────────────────────

async def fetch_page(url: str) -> tuple[str, str, str]:
    """
    Fetch a single product page using the best available tool.

    Returns:
        (platform, content, tool_used)

    Tool selection is site-experience-aware and auto-falls-back.
    Every attempt is recorded to improve future decisions.
    """
    platform = detect_platform(url)
    cdp_available = await _cdp.health()
    tool_chain = decide_tool(url, cdp_available)
    errors = []

    for tool in tool_chain:
        try:
            if tool == ToolChoice.CDP:
                content = await _fetch_via_cdp(url, platform)

            elif tool == ToolChoice.WEB_FETCH:
                content = fetch_via_web_fetch(url)

            elif tool == ToolChoice.JINA:
                content = await fetch_via_jina(url)

            elif tool == ToolChoice.CURL:
                content = await fetch_via_curl(url)

            else:
                continue

            if content and len(content.strip()) > 150:
                record_success(url, tool)
                return platform, content, tool

            errors.append(f"{tool}: content too short ({len(content.strip())} chars)")
            record_failure(url, tool, "content too short")

        except Exception as e:
            errors.append(f"{tool}: {e}")
            record_failure(url, tool, str(e))

    raise RuntimeError(
        f"All tools failed for {url}:\n" + "\n".join(f"  • {e}" for e in errors)
    )


# ── Parallel fetch ─────────────────────────────────────────────────────────────

async def fetch_pages_parallel(
    urls: list[str],
    max_concurrent: int = 4,
) -> list[dict]:
    """
    Fetch multiple pages concurrently using asyncio + CDP tab isolation.
    Each tab is independent; CDP proxy manages session sharing automatically.

    Returns list of:
      { url, platform, content, tool_used, success, error }
    """
    semaphore = asyncio.Semaphore(max_concurrent)

    async def _fetch_one(url: str) -> dict:
        async with semaphore:
            try:
                platform, content, tool = await fetch_page(url)
                return {
                    "url": url, "platform": platform,
                    "content": content, "tool_used": tool,
                    "success": True, "error": None,
                }
            except Exception as e:
                return {
                    "url": url, "platform": detect_platform(url),
                    "content": "", "tool_used": "none",
                    "success": False, "error": str(e),
                }

    tasks = [_fetch_one(url) for url in urls]
    return await asyncio.gather(*tasks)


# ── Amazon search ──────────────────────────────────────────────────────────────

async def search_amazon(keyword: str, marketplace: str = "amazon.com") -> list[dict]:
    """
    Search Amazon for products matching a keyword.
    Uses CDP if available (real browser, anti-bot bypass),
    falls back to Claude web_search tool.
    """
    search_url = f"https://www.{marketplace}/s?k={keyword.replace(' ', '+')}&ref=nb_sb_noss"
    cdp_available = await _cdp.health()

    if cdp_available:
        try:
            candidates = await _search_amazon_cdp(search_url, marketplace)
            if candidates:
                return candidates
        except Exception:
            pass

    # Fallback: Claude web_search → parse JSON
    return await _search_amazon_claude(keyword, marketplace)


async def _search_amazon_cdp(search_url: str, marketplace: str) -> list[dict]:
    """Extract Amazon search results directly from DOM via CDP."""
    exp = get_site_experience(f"https://{marketplace}")
    search_sel = exp.get("search_selectors", {
        "results": "[data-component-type='s-search-result']",
        "title": "h2 a span",
        "price": ".a-price .a-offscreen",
        "rating": ".a-icon-star-small .a-icon-alt",
        "review_count": ".a-size-small .a-link-normal",
        "url": "h2 a",
    })

    async with ManagedTab(_cdp, search_url) as tab_id:
        await asyncio.sleep(2)
        await _cdp.scroll(tab_id, "down")
        await asyncio.sleep(0.8)

        js = f"""
        Array.from(document.querySelectorAll({repr(search_sel['results'])}))
          .slice(0, 15)
          .map(el => {{
            const titleEl = el.querySelector({repr(search_sel['title'])});
            const priceEl = el.querySelector({repr(search_sel['price'])});
            const ratingEl = el.querySelector({repr(search_sel['rating'])});
            const reviewEl = el.querySelector({repr(search_sel['review_count'])});
            const urlEl = el.querySelector({repr(search_sel['url'])});
            const asin = el.getAttribute('data-asin') || '';
            return {{
              title: titleEl?.textContent?.trim() || '',
              price: priceEl?.textContent?.replace(/[^0-9.]/g,'') || '',
              rating: ratingEl?.textContent?.split(' ')[0] || '',
              review_count: reviewEl?.textContent?.replace(/[^0-9,]/g,'').replace(',','') || '',
              asin: asin,
              url: urlEl ? 'https://www.amazon.com' + urlEl.getAttribute('href') : '',
            }};
          }})
          .filter(p => p.title)
        """
        raw = await _cdp.eval(tab_id, js)

    if not isinstance(raw, list):
        return []

    results = []
    for item in raw:
        try:
            results.append({
                "title": item.get("title", ""),
                "price": float(item["price"]) if item.get("price") else None,
                "rating": float(item["rating"]) if item.get("rating") else None,
                "review_count": int(item["review_count"].replace(",", "")) if item.get("review_count") else None,
                "asin": item.get("asin", ""),
                "url": item.get("url", ""),
            })
        except (ValueError, TypeError):
            results.append(item)

    return results


async def _search_amazon_claude(keyword: str, marketplace: str) -> list[dict]:
    """Search Amazon via Claude web_search tool, parse JSON from response."""
    from app.ai.client import search_amazon_products
    raw_text = search_amazon_products(keyword, marketplace)
    match = re.search(r"\[[\s\S]*?\]", raw_text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    # Ask Claude to re-parse if JSON extraction failed
    from app.ai.client import complete
    prompt = f"""Extract product listings from this text and return a JSON array.
Each item: {{ title, price (number), rating (number), review_count (number), asin, url }}
Return ONLY the JSON array.

TEXT:
{raw_text[:4000]}"""
    text = complete(prompt, max_tokens=2048)
    match = re.search(r"\[[\s\S]*?\]", text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return []


# ── General web search ─────────────────────────────────────────────────────────

async def search_web(query: str) -> str:
    """Run a general web search. Returns text summary."""
    try:
        return search_via_web_search(query)
    except Exception as e:
        return f"Search failed: {e}"
