"""
Site Experience System — mirrors web-access references/site-patterns + match-site.mjs

Every time we successfully (or fail to) crawl a domain, we update a knowledge entry.
On the next crawl of the same domain, we load this entry first and adapt our strategy.

Storage: Redis hash  "site_exp:{domain}"
         + JSON file backend/app/web_access/site_patterns/{domain}.json  (persistence)

Built-in seed data for the most common e-commerce platforms.
"""
import json
import re
import os
from datetime import datetime
from pathlib import Path
import redis as redis_lib
from app.config import settings

r = redis_lib.from_url(settings.REDIS_URL)

PATTERNS_DIR = Path(__file__).parent / "site_patterns"
PATTERNS_DIR.mkdir(exist_ok=True)

# ── Built-in seed patterns ─────────────────────────────────────────────────────

SEED_PATTERNS: dict[str, dict] = {
    "1688.com": {
        "domain": "1688.com",
        "aliases": ["1688", "detail.1688.com", "offer.1688.com"],
        "tool": "cdp",                       # preferred tool
        "requires_login": False,
        "js_heavy": True,
        "anti_scrape": True,
        "wait_seconds": 3,
        "scroll_needed": True,
        "selectors": {
            "title": ".mod-detail-header h1, #mod-detail-title",
            "price": ".price-value, .mod-price",
            "images": ".detail-gallery-img img, .main-pic img",
            "specs": ".mod-detail-attributes .attr-item",
            "description": "#mod-detail-description",
        },
        "known_issues": [
            "Requires scroll to load price tiers",
            "Login wall for some supplier pages",
            "Dynamic JS rendering — httpx won't work",
        ],
        "success_rate": 0.75,
        "last_updated": "2025-01-01",
    },
    "alibaba.com": {
        "domain": "alibaba.com",
        "aliases": ["alibaba", "www.alibaba.com"],
        "tool": "cdp",
        "requires_login": False,
        "js_heavy": True,
        "anti_scrape": False,
        "wait_seconds": 2,
        "scroll_needed": True,
        "selectors": {
            "title": ".product-title, .title-text",
            "price": ".price, .product-price",
            "images": ".product-image img, .gallery-thumbnail img",
        },
        "known_issues": ["Price tiers require scroll"],
        "success_rate": 0.80,
        "last_updated": "2025-01-01",
    },
    "amazon.com": {
        "domain": "amazon.com",
        "aliases": ["amazon", "www.amazon.com", "amazon.co.uk", "amazon.de", "amazon.co.jp"],
        "tool": "cdp",
        "requires_login": False,
        "js_heavy": True,
        "anti_scrape": True,
        "wait_seconds": 2,
        "scroll_needed": False,
        "selectors": {
            "title": "#productTitle",
            "price": ".a-price .a-offscreen, #priceblock_ourprice",
            "rating": "#acrPopover",
            "review_count": "#acrCustomerReviewText",
            "bullets": "#feature-bullets .a-list-item",
            "images": "#altImages img",
            "asin": "input[name=ASIN]",
        },
        "search_selectors": {
            "results": "[data-component-type='s-search-result']",
            "title": "h2 a span",
            "price": ".a-price .a-offscreen",
            "rating": ".a-icon-star-small .a-icon-alt",
            "review_count": ".a-size-small .a-link-normal",
            "url": "h2 a",
        },
        "known_issues": [
            "Bot detection on repeated requests from same IP",
            "JavaScript required for price display",
            "Captcha on high-frequency access",
        ],
        "success_rate": 0.70,
        "last_updated": "2025-01-01",
    },
    "shopify": {
        "domain": "shopify",
        "aliases": ["myshopify.com"],
        "tool": "web_fetch",
        "requires_login": False,
        "js_heavy": False,
        "anti_scrape": False,
        "wait_seconds": 1,
        "scroll_needed": False,
        "selectors": {
            "title": "h1.product-title, .product__title",
            "price": ".price, .product__price",
        },
        "known_issues": [],
        "success_rate": 0.90,
        "last_updated": "2025-01-01",
    },
}


# ── Core functions ─────────────────────────────────────────────────────────────

def _domain_key(url_or_domain: str) -> str:
    """Extract canonical domain from a URL or domain string."""
    url_or_domain = url_or_domain.lower().strip()
    # Strip protocol
    url_or_domain = re.sub(r"^https?://", "", url_or_domain)
    # Take host part
    host = url_or_domain.split("/")[0].split("?")[0]
    # Remove www.
    host = re.sub(r"^www\.", "", host)
    return host


def _match_domain(query: str) -> str | None:
    """
    Find the best matching pattern key for a URL/domain string.
    Mirrors match-site.mjs logic: checks domain + aliases.
    """
    query_clean = _domain_key(query)
    for key, pat in SEED_PATTERNS.items():
        candidates = [key] + pat.get("aliases", [])
        for alias in candidates:
            alias_clean = _domain_key(alias)
            if alias_clean in query_clean or query_clean in alias_clean:
                return key
    return None


def get_site_experience(url: str) -> dict:
    """
    Load accumulated experience for a domain.
    Priority: Redis (runtime updates) > seed patterns > empty dict
    """
    domain = _domain_key(url)
    redis_key = f"site_exp:{domain}"

    # 1. Try Redis
    raw = r.get(redis_key)
    if raw:
        return json.loads(raw)

    # 2. Try disk cache
    cache_file = PATTERNS_DIR / f"{domain}.json"
    if cache_file.exists():
        exp = json.loads(cache_file.read_text())
        r.set(redis_key, json.dumps(exp), ex=86400 * 7)
        return exp

    # 3. Try seed patterns (with alias matching)
    matched_key = _match_domain(url)
    if matched_key:
        exp = dict(SEED_PATTERNS[matched_key])
        r.set(redis_key, json.dumps(exp), ex=86400 * 7)
        return exp

    return {}


def update_site_experience(url: str, update: dict) -> None:
    """
    Merge new crawl results into the domain's experience record.
    Called after every crawl attempt (success or failure).
    """
    domain = _domain_key(url)
    redis_key = f"site_exp:{domain}"

    exp = get_site_experience(url) or {"domain": domain, "crawl_history": []}
    exp.update(update)
    exp["last_updated"] = datetime.utcnow().isoformat()

    # Update success rate rolling average
    history = exp.setdefault("crawl_history", [])
    history.append({
        "ts": datetime.utcnow().isoformat(),
        "success": update.get("last_success", False),
        "tool": update.get("last_tool_used", ""),
    })
    exp["crawl_history"] = history[-20:]  # keep last 20

    successes = sum(1 for h in history if h.get("success"))
    exp["success_rate"] = round(successes / len(history), 2)

    r.set(redis_key, json.dumps(exp), ex=86400 * 7)

    # Persist to disk
    cache_file = PATTERNS_DIR / f"{domain}.json"
    cache_file.write_text(json.dumps(exp, indent=2, ensure_ascii=False))


def record_success(url: str, tool_used: str, notes: str = "") -> None:
    update_site_experience(url, {
        "last_success": True,
        "last_tool_used": tool_used,
        "last_success_notes": notes,
    })


def record_failure(url: str, tool_used: str, error: str = "") -> None:
    update_site_experience(url, {
        "last_success": False,
        "last_tool_used": tool_used,
        "last_failure_error": error,
    })


def get_preferred_tool(url: str) -> str:
    """
    Return the recommended tool for this URL based on experience.
    Falls back to 'cdp' for unknown dynamic sites.
    """
    exp = get_site_experience(url)
    if not exp:
        return "cdp"

    # If site recently failed with CDP, try web_fetch
    history = exp.get("crawl_history", [])
    recent = history[-3:] if history else []
    cdp_recent_failures = sum(
        1 for h in recent if h.get("tool") == "cdp" and not h.get("success")
    )
    if cdp_recent_failures >= 2:
        return "web_fetch"

    return exp.get("tool", "cdp")


def get_wait_time(url: str) -> float:
    exp = get_site_experience(url)
    return float(exp.get("wait_seconds", 2))


def get_selectors(url: str) -> dict:
    exp = get_site_experience(url)
    return exp.get("selectors", {})


def needs_scroll(url: str) -> bool:
    exp = get_site_experience(url)
    return bool(exp.get("scroll_needed", True))


def list_all_patterns() -> list[dict]:
    """List all known site patterns (seed + learned)."""
    all_patterns = {}
    # Seed
    for k, v in SEED_PATTERNS.items():
        all_patterns[k] = v
    # Redis overrides
    for key in r.scan_iter("site_exp:*"):
        domain = key.decode().replace("site_exp:", "")
        raw = r.get(key)
        if raw:
            all_patterns[domain] = json.loads(raw)
    return list(all_patterns.values())
