"""
Smart tool selection strategy — mirrors SKILL.md philosophy.

Tools available (in order of capability):
  cdp       → Real Chrome browser (JS, login, anti-scrape) — best but needs proxy
  web_fetch → Claude web_search tool — good for dynamic pages w/o proxy
  jina      → r.jina.ai/{url} — converts pages to clean Markdown (20 RPM)
  curl      → Plain httpx — fast for static pages
  search    → Claude web_search tool for keyword discovery

Selection logic (matches SKILL.md):
  1. Load site experience to know what worked before
  2. If CDP proxy available → prefer CDP for JS-heavy / anti-scrape sites
  3. If page is static/simple → curl first (fastest)
  4. If CDP unavailable and page is dynamic → web_fetch (Claude tool)
  5. Jina as enrichment layer for complex pages that need clean Markdown
"""
import httpx
from app.web_access.site_experience import (
    get_site_experience,
    get_preferred_tool,
)


# ── Jina reader ────────────────────────────────────────────────────────────────

JINA_BASE = "https://r.jina.ai"
JINA_RPM_LIMIT = 20  # Jina free tier limit


async def fetch_via_jina(url: str) -> str:
    """
    Convert any webpage to clean Markdown via Jina Reader.
    Great for article/product pages; respects 20 RPM limit.
    Returns Markdown string.
    """
    jina_url = f"{JINA_BASE}/{url}"
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as c:
        headers = {
            "Accept": "text/plain",
            "X-Return-Format": "markdown",
        }
        r = await c.get(jina_url, headers=headers)
        r.raise_for_status()
        return r.text


# ── curl (plain httpx) ─────────────────────────────────────────────────────────

async def fetch_via_curl(url: str) -> str:
    """
    Plain HTTP GET with a realistic browser UA.
    Works for static pages; fails on JS-rendered or bot-protected sites.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as c:
        r = await c.get(url, headers=headers)
        r.raise_for_status()
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(r.text, "lxml")
        # Remove script/style noise
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        return soup.get_text(separator="\n", strip=True)


# ── Claude web_search tool ─────────────────────────────────────────────────────

def fetch_via_web_fetch(url: str) -> str:
    """Fetch a URL via Claude's web_search tool (Anthropic API)."""
    from app.ai.client import fetch_page_with_web_access
    return fetch_page_with_web_access(url)


def search_via_web_search(query: str) -> str:
    """Run a web search query via Claude's web_search tool."""
    from app.ai.client import complete_with_tools, WEB_SEARCH_TOOL
    return complete_with_tools(
        f"Search for: {query}\nReturn a comprehensive summary of the top results.",
        WEB_SEARCH_TOOL,
        max_tokens=2048,
    )


# ── Strategy decision engine ───────────────────────────────────────────────────

class ToolChoice:
    CDP = "cdp"
    WEB_FETCH = "web_fetch"
    JINA = "jina"
    CURL = "curl"


def decide_tool(url: str, cdp_available: bool) -> list[str]:
    """
    Return an ordered list of tools to try for this URL.
    First item is the preferred tool; rest are fallbacks.

    Mirrors SKILL.md decision logic:
    - JS-heavy / anti-scrape / login → CDP first
    - Static / simple → curl first (fast)
    - CDP down → web_fetch as best dynamic option
    - Jina used as enrichment, not primary
    """
    exp = get_site_experience(url)
    preferred = get_preferred_tool(url)
    js_heavy = exp.get("js_heavy", True)
    anti_scrape = exp.get("anti_scrape", False)
    requires_login = exp.get("requires_login", False)

    if requires_login:
        # Login-required: CDP only (uses user's real session)
        return [ToolChoice.CDP]

    if cdp_available and (js_heavy or anti_scrape):
        return [ToolChoice.CDP, ToolChoice.WEB_FETCH, ToolChoice.JINA, ToolChoice.CURL]

    if not js_heavy and not anti_scrape:
        # Static page — curl is fastest
        return [ToolChoice.CURL, ToolChoice.JINA, ToolChoice.WEB_FETCH, ToolChoice.CDP]

    # Default: prefer whatever worked before, then fallback chain
    order = {
        ToolChoice.CDP: [ToolChoice.CDP, ToolChoice.WEB_FETCH, ToolChoice.JINA, ToolChoice.CURL],
        ToolChoice.WEB_FETCH: [ToolChoice.WEB_FETCH, ToolChoice.CDP, ToolChoice.JINA, ToolChoice.CURL],
        ToolChoice.JINA: [ToolChoice.JINA, ToolChoice.WEB_FETCH, ToolChoice.CDP, ToolChoice.CURL],
        ToolChoice.CURL: [ToolChoice.CURL, ToolChoice.JINA, ToolChoice.WEB_FETCH, ToolChoice.CDP],
    }
    chain = order.get(preferred, order[ToolChoice.CDP])

    # If CDP not available, remove it from chain
    if not cdp_available:
        chain = [t for t in chain if t != ToolChoice.CDP]

    return chain
