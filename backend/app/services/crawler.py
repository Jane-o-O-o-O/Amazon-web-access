"""
Crawler service — 3-layer fallback strategy:

  Layer 1: web-access CDP proxy (localhost:3456)
           → real browser, preserves login, handles JS/anti-scrape/1688
  Layer 2: Claude web_search tool (web-access)
           → Claude fetches and summarizes the page via Anthropic servers
  Layer 3: httpx + BeautifulSoup
           → plain HTTP for static pages only

Each layer falls back to the next on failure.
"""
import re
import json
import httpx
from bs4 import BeautifulSoup
from app.config import settings


# ─── Platform detection ───────────────────────────────────────────────────────

def detect_platform(url: str) -> str:
    if "1688.com" in url:
        return "1688"
    if "alibaba.com" in url:
        return "alibaba"
    if "amazon.com" in url or "amazon." in url:
        return "amazon"
    return "unknown"


# ─── Layer 1: CDP proxy (web-access) ─────────────────────────────────────────

class CDPCrawler:
    """
    HTTP client for the web-access CDP proxy (http://localhost:3456).
    Operates inside the user's real Chrome browser — full JS rendering,
    login state, cookies, and anti-scrape bypass.

    Proxy API:
      GET  /new?url=<url>           → { id: "<tab_id>" }
      POST /eval?target=<id>        → body: JS code string → result
      POST /click?target=<id>       → body: CSS selector
      POST /clickAt?target=<id>     → body: { x, y } (real mouse)
      GET  /screenshot?target=<id>&file=<path>
      GET  /scroll?target=<id>&direction=<down|up>
      GET  /close?target=<id>
    """

    def __init__(self, base_url: str | None = None):
        self.base = (base_url or settings.CDP_PROXY_URL).rstrip("/")

    async def is_available(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=3) as c:
                r = await c.get(f"{self.base}/targets")
                return r.status_code < 500
        except Exception:
            return False

    async def open_tab(self, url: str) -> str:
        """Open a new browser tab and return its tab_id."""
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.get(f"{self.base}/new", params={"url": url})
            r.raise_for_status()
            data = r.json()
            return data.get("id") or data.get("target") or str(data)

    async def get_text(self, tab_id: str) -> str:
        """Extract all visible text from the page via JS eval."""
        js = "document.body ? document.body.innerText : document.documentElement.innerText"
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.post(f"{self.base}/eval", params={"target": tab_id}, content=js)
            r.raise_for_status()
            return r.text

    async def get_html(self, tab_id: str) -> str:
        """Get full outer HTML for deep parsing."""
        js = "document.documentElement.outerHTML"
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.post(f"{self.base}/eval", params={"target": tab_id}, content=js)
            r.raise_for_status()
            return r.text

    async def click(self, tab_id: str, selector: str) -> None:
        """Trigger a JS click on a CSS selector."""
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.post(f"{self.base}/click", params={"target": tab_id}, content=selector)
            r.raise_for_status()

    async def scroll(self, tab_id: str, direction: str = "down") -> None:
        async with httpx.AsyncClient(timeout=10) as c:
            await c.get(f"{self.base}/scroll", params={"target": tab_id, "direction": direction})

    async def screenshot(self, tab_id: str, file_path: str) -> None:
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.get(f"{self.base}/screenshot", params={"target": tab_id, "file": file_path})
            r.raise_for_status()

    async def close(self, tab_id: str) -> None:
        async with httpx.AsyncClient(timeout=10) as c:
            await c.get(f"{self.base}/close", params={"target": tab_id})

    async def fetch_page(self, url: str) -> str:
        """
        Full flow: open tab → wait for load → scroll → extract text → close.
        Returns page text content.
        """
        import asyncio
        tab_id = await self.open_tab(url)
        try:
            await asyncio.sleep(3)       # wait for JS render
            await self.scroll(tab_id)    # trigger lazy loads
            await asyncio.sleep(1)
            text = await self.get_text(tab_id)
            return text
        finally:
            await self.close(tab_id)


# ─── Layer 2: Claude web_search tool ─────────────────────────────────────────

def _layer2_fetch(url: str) -> str:
    from app.ai.client import fetch_page_with_web_access
    return fetch_page_with_web_access(url)


# ─── Layer 3: httpx + BeautifulSoup (static only) ────────────────────────────

async def _layer3_fetch(url: str) -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as c:
        r = await c.get(url, headers=headers)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")
        return soup.get_text(separator="\n", strip=True)


# ─── Public API ───────────────────────────────────────────────────────────────

_cdp = CDPCrawler()


async def crawl_product_page(url: str) -> tuple[str, str]:
    """
    Fetch a product page using the best available method.
    Returns (platform, text_content).
    """
    platform = detect_platform(url)
    errors = []

    # Layer 1: CDP proxy
    if settings.CDP_ENABLED:
        try:
            if await _cdp.is_available():
                content = await _cdp.fetch_page(url)
                if content and len(content.strip()) > 200:
                    return platform, content
                errors.append("CDP: empty response")
            else:
                errors.append("CDP: proxy not running")
        except Exception as e:
            errors.append(f"CDP: {e}")

    # Layer 2: Claude web_search
    try:
        content = _layer2_fetch(url)
        if content and len(content.strip()) > 100:
            return platform, content
        errors.append("web_search: empty response")
    except Exception as e:
        errors.append(f"web_search: {e}")

    # Layer 3: httpx static fallback
    try:
        content = await _layer3_fetch(url)
        return platform, content
    except Exception as e:
        errors.append(f"httpx: {e}")

    raise RuntimeError(f"All crawl layers failed for {url}: {'; '.join(errors)}")


async def search_amazon_candidates(keyword: str, marketplace: str = "amazon.com") -> list[dict]:
    """
    Search Amazon for candidate products.
    Returns a list of candidate product dicts.
    """
    from app.ai.client import search_amazon_products

    # Try CDP first — search directly in real browser
    if settings.CDP_ENABLED:
        try:
            if await _cdp.is_available():
                search_url = f"https://www.{marketplace}/s?k={keyword.replace(' ', '+')}"
                content = await _cdp.fetch_page(search_url)
                # Let Claude parse the search results page
                from app.ai.client import extract_product_info
                # Use a simple parse prompt for search results
                parsed = _parse_amazon_search_results(content)
                if parsed:
                    return parsed
        except Exception:
            pass

    # Fallback: Claude web_search tool
    raw_text = search_amazon_products(keyword, marketplace)
    match = re.search(r"\[[\s\S]*?\]", raw_text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return []


def _parse_amazon_search_results(content: str) -> list[dict]:
    """
    Ask Claude to parse Amazon search result page text into a structured list.
    """
    from app.ai.client import complete
    prompt = f"""Extract Amazon product listings from this search result page text.
Return a JSON array of up to 10 products. Each object must have:
  title, price (number), rating (number), review_count (number), asin, url

Only return the JSON array, nothing else.

PAGE TEXT:
{content[:6000]}
"""
    text = complete(prompt, max_tokens=2048)
    match = re.search(r"\[[\s\S]*?\]", text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return []
