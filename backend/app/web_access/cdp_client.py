"""
Full CDP Proxy HTTP client.

Mirrors every endpoint exposed by web-access/scripts/cdp-proxy.mjs:

  Navigation:   /new  /navigate  /back
  Interaction:  /click  /clickAt  /setFiles  /scroll
  Scripting:    /eval
  Content:      /screenshot  /info
  Management:   /targets  /close  /health
"""
import asyncio
import httpx
from dataclasses import dataclass
from typing import Any
from app.config import settings


@dataclass
class TabInfo:
    id: str
    url: str
    title: str


class CDPClient:
    """
    Async HTTP client for the web-access CDP proxy.
    Each method maps 1-to-1 with a proxy endpoint.
    """

    def __init__(self, base_url: str | None = None):
        self.base = (base_url or settings.CDP_PROXY_URL).rstrip("/")
        self._http = httpx.AsyncClient(timeout=45)

    # ── Lifecycle ──────────────────────────────────────────────────────────

    async def health(self) -> bool:
        """Return True if the proxy is reachable and healthy."""
        try:
            r = await self._http.get(f"{self.base}/health")
            return r.status_code == 200
        except Exception:
            return False

    async def targets(self) -> list[TabInfo]:
        """List all open browser tabs managed by the proxy."""
        r = await self._http.get(f"{self.base}/targets")
        r.raise_for_status()
        tabs = r.json() if r.text else []
        return [TabInfo(id=t.get("id",""), url=t.get("url",""), title=t.get("title","")) for t in tabs]

    async def close(self, tab_id: str) -> None:
        """Close a tab."""
        await self._http.get(f"{self.base}/close", params={"target": tab_id})

    # ── Navigation ─────────────────────────────────────────────────────────

    async def new_tab(self, url: str) -> str:
        """Open a new background tab and return its tab_id."""
        r = await self._http.get(f"{self.base}/new", params={"url": url})
        r.raise_for_status()
        data = r.json()
        return data.get("id") or data.get("target") or list(data.values())[0]

    async def navigate(self, tab_id: str, url: str) -> None:
        """Navigate an existing tab to a new URL (waits for page load)."""
        r = await self._http.get(
            f"{self.base}/navigate",
            params={"target": tab_id, "url": url},
        )
        r.raise_for_status()

    async def back(self, tab_id: str) -> None:
        """Go back one step in the tab's history."""
        await self._http.get(f"{self.base}/back", params={"target": tab_id})

    # ── Scripting ──────────────────────────────────────────────────────────

    async def eval(self, tab_id: str, js: str) -> Any:
        """
        Execute arbitrary JavaScript in the page context.
        Supports async/await via awaitPromise.
        Return values must be serializable (str, int, dict, list).
        """
        r = await self._http.post(
            f"{self.base}/eval",
            params={"target": tab_id},
            content=js,
            headers={"Content-Type": "text/plain"},
        )
        r.raise_for_status()
        try:
            return r.json()
        except Exception:
            return r.text

    # ── Interaction ────────────────────────────────────────────────────────

    async def click(self, tab_id: str, selector: str) -> None:
        """
        JS-based click on a CSS selector.
        Lighter weight, good for normal buttons/links.
        """
        r = await self._http.post(
            f"{self.base}/click",
            params={"target": tab_id},
            content=selector,
            headers={"Content-Type": "text/plain"},
        )
        r.raise_for_status()

    async def click_at(self, tab_id: str, x: int, y: int) -> None:
        """
        Real CDP mouse event at pixel coordinates.
        Bypasses anti-automation detection (e.g. file dialogs, CAPTCHA buttons).
        """
        import json
        r = await self._http.post(
            f"{self.base}/clickAt",
            params={"target": tab_id},
            content=json.dumps({"x": x, "y": y}),
            headers={"Content-Type": "application/json"},
        )
        r.raise_for_status()

    async def set_files(self, tab_id: str, selector: str, file_paths: list[str]) -> None:
        """
        Set file input values without opening a file dialog.
        """
        import json
        r = await self._http.post(
            f"{self.base}/setFiles",
            params={"target": tab_id},
            content=json.dumps({"selector": selector, "files": file_paths}),
            headers={"Content-Type": "application/json"},
        )
        r.raise_for_status()

    async def scroll(self, tab_id: str, direction: str = "down", y: int | None = None) -> None:
        """
        Scroll the page. Proxy waits 800ms after scroll for lazy loading.
        direction: down | up | top | bottom
        y: optional pixel offset (overrides direction)
        """
        params: dict = {"target": tab_id, "direction": direction}
        if y is not None:
            params["y"] = y
        await self._http.get(f"{self.base}/scroll", params=params)

    # ── Content extraction ─────────────────────────────────────────────────

    async def get_text(self, tab_id: str) -> str:
        """Extract all visible text via JS innerText."""
        return await self.eval(tab_id, "document.body?.innerText ?? document.documentElement.innerText")

    async def get_html(self, tab_id: str) -> str:
        """Get full outer HTML."""
        return await self.eval(tab_id, "document.documentElement.outerHTML")

    async def get_title(self, tab_id: str) -> str:
        return await self.eval(tab_id, "document.title")

    async def get_url(self, tab_id: str) -> str:
        return await self.eval(tab_id, "location.href")

    async def query_selector(self, tab_id: str, selector: str, attribute: str = "textContent") -> str:
        """Extract a single attribute from the first matching element."""
        js = f"document.querySelector({repr(selector)})?.{attribute} ?? ''"
        return await self.eval(tab_id, js)

    async def query_selector_all(self, tab_id: str, selector: str, attribute: str = "textContent") -> list[str]:
        """Extract an attribute from ALL matching elements."""
        js = f"Array.from(document.querySelectorAll({repr(selector)})).map(el => el.{attribute})"
        result = await self.eval(tab_id, js)
        return result if isinstance(result, list) else []

    async def screenshot(self, tab_id: str, file_path: str) -> None:
        """Save a screenshot of the current tab to a local file."""
        r = await self._http.get(
            f"{self.base}/screenshot",
            params={"target": tab_id, "file": file_path},
        )
        r.raise_for_status()

    async def info(self, tab_id: str) -> dict:
        """Get page metadata (url, title, ready state)."""
        r = await self._http.get(f"{self.base}/info", params={"target": tab_id})
        r.raise_for_status()
        try:
            return r.json()
        except Exception:
            return {"raw": r.text}

    # ── High-level helpers ─────────────────────────────────────────────────

    async def wait_for_load(self, tab_id: str, timeout: float = 15.0) -> None:
        """Poll document.readyState until 'complete' or timeout."""
        deadline = asyncio.get_event_loop().time() + timeout
        while asyncio.get_event_loop().time() < deadline:
            state = await self.eval(tab_id, "document.readyState")
            if state == "complete":
                return
            await asyncio.sleep(0.5)

    async def wait_for_selector(self, tab_id: str, selector: str, timeout: float = 10.0) -> bool:
        """Wait until a CSS selector appears in the DOM."""
        deadline = asyncio.get_event_loop().time() + timeout
        js = f"!!document.querySelector({repr(selector)})"
        while asyncio.get_event_loop().time() < deadline:
            found = await self.eval(tab_id, js)
            if found:
                return True
            await asyncio.sleep(0.5)
        return False

    async def extract_product_data(self, tab_id: str, platform: str) -> dict:
        """
        Platform-aware structured data extraction via JS.
        Tries structured selectors first; falls back to full innerText.
        """
        extractors = {
            "1688": """({
                title: document.querySelector('.mod-detail-header h1,#mod-detail-title')?.innerText,
                price: document.querySelector('.price-value,.mod-price')?.innerText,
                images: Array.from(document.querySelectorAll('.detail-gallery-img img,.main-pic img')).map(i=>i.src),
                specs: Object.fromEntries(Array.from(document.querySelectorAll('.mod-detail-attributes .attr-item')).map(el=>[el.querySelector('.attr-name')?.textContent?.trim(), el.querySelector('.attr-value')?.textContent?.trim()])),
                description: document.querySelector('#mod-detail-description,.content-detail')?.innerText
            })""",
            "amazon": """({
                title: document.querySelector('#productTitle')?.innerText?.trim(),
                price: document.querySelector('.a-price .a-offscreen,#priceblock_ourprice')?.innerText,
                rating: document.querySelector('#acrPopover')?.title,
                review_count: document.querySelector('#acrCustomerReviewText')?.innerText,
                bullets: Array.from(document.querySelectorAll('#feature-bullets .a-list-item')).map(el=>el.innerText.trim()),
                images: Array.from(document.querySelectorAll('#altImages img')).map(i=>i.src.replace(/._.*_./,'._AC_SL1500_.'))
            })""",
            "alibaba": """({
                title: document.querySelector('.product-title,.title-text')?.innerText,
                price: document.querySelector('.price,.product-price')?.innerText,
                images: Array.from(document.querySelectorAll('.product-image img,.gallery-thumbnail img')).map(i=>i.src)
            })""",
        }
        js = extractors.get(platform, "null")
        structured = await self.eval(tab_id, js)
        if not structured:
            structured = {}
        structured["_raw_text"] = await self.get_text(tab_id)
        return structured

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        await self._http.aclose()


# ── Managed tab context manager ────────────────────────────────────────────────

class ManagedTab:
    """
    Context manager that opens a tab and guarantees cleanup.

    async with ManagedTab(client, url) as tab_id:
        content = await client.get_text(tab_id)
    """

    def __init__(self, client: CDPClient, url: str):
        self.client = client
        self.url = url
        self.tab_id: str = ""

    async def __aenter__(self) -> str:
        self.tab_id = await self.client.new_tab(self.url)
        return self.tab_id

    async def __aexit__(self, *_):
        if self.tab_id:
            try:
                await self.client.close(self.tab_id)
            except Exception:
                pass
