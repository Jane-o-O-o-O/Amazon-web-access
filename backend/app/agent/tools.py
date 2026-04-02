"""
Agent tool definitions.

Each tool is callable by the coordinator agent.
Tools wrap the web_access module and service layer.

Tool schema: Anthropic tool_use format { name, description, input_schema }
Tool handlers: sync functions(dict) -> dict
"""
import json
import asyncio
from typing import Callable


# ─── Tool schemas (what Claude sees) ─────────────────────────────────────────

TOOL_SCHEMAS = [
    {
        "name": "crawl_product",
        "description": (
            "Fetch a single product page (1688 / Alibaba / Amazon / any URL). "
            "Automatically selects the best tool: CDP real browser → Jina → web_fetch → curl. "
            "Returns structured text content including title, price, specs, images."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Full product page URL"},
            },
            "required": ["url"],
        },
    },
    {
        "name": "crawl_pages_parallel",
        "description": (
            "Fetch multiple product pages concurrently (up to 8 at once). "
            "Use this when you need to crawl several Amazon candidate pages at the same time. "
            "Returns a list of results, one per URL."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "urls": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of URLs to fetch in parallel",
                },
                "max_concurrent": {
                    "type": "integer",
                    "description": "Max simultaneous fetches (default: 4)",
                    "default": 4,
                },
            },
            "required": ["urls"],
        },
    },
    {
        "name": "search_amazon",
        "description": (
            "Search Amazon for products matching a keyword. "
            "Uses CDP browser if available for best results, falls back to web_search. "
            "Returns a structured list of candidates with title, price, rating, ASIN, URL."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "keyword": {"type": "string", "description": "Search keyword (English, from product title)"},
                "marketplace": {
                    "type": "string",
                    "description": "Amazon domain: amazon.com / amazon.co.uk / amazon.de / amazon.co.jp",
                    "default": "amazon.com",
                },
            },
            "required": ["keyword"],
        },
    },
    {
        "name": "search_web",
        "description": "Run a general web search query. Returns a text summary of top results.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_site_experience",
        "description": (
            "Look up accumulated crawling experience for a domain. "
            "Returns known selectors, preferred tool, success rate, and known issues. "
            "Useful before deciding how to crawl a site."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL or domain to look up"},
            },
            "required": ["url"],
        },
    },
    {
        "name": "parse_product",
        "description": "Parse raw page content into structured product fields using Claude LLM.",
        "input_schema": {
            "type": "object",
            "properties": {
                "platform": {"type": "string", "description": "1688 | alibaba | amazon | unknown"},
                "content": {"type": "string", "description": "Raw page text or structured content"},
            },
            "required": ["platform", "content"],
        },
    },
    {
        "name": "match_products",
        "description": (
            "Score similarity between a source product and an Amazon candidate. "
            "Returns match_score (0-100), match_level, same/diff points, and reasoning."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "source": {"type": "object", "description": "Source product dict"},
                "target": {"type": "object", "description": "Amazon candidate product dict"},
            },
            "required": ["source", "target"],
        },
    },
    {
        "name": "analyze_competitors",
        "description": "Generate a competitor analysis report from a list of Amazon products.",
        "input_schema": {
            "type": "object",
            "properties": {
                "competitors": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "List of Amazon competitor product dicts",
                },
            },
            "required": ["competitors"],
        },
    },
    {
        "name": "calculate_margin",
        "description": "Calculate profit margins given cost parameters and a selling price.",
        "input_schema": {
            "type": "object",
            "properties": {
                "cost_params": {
                    "type": "object",
                    "description": "Keys: purchasePrice, domesticShipping, internationalShipping, fbaFee, commissionRate, adsRate, taxRate, exchangeRate",
                },
                "sell_price": {"type": "number", "description": "Amazon selling price in USD"},
            },
            "required": ["cost_params", "sell_price"],
        },
    },
    {
        "name": "generate_listing",
        "description": "Generate a full Amazon listing (title, bullets, description, search terms) from product specs and competitor insights.",
        "input_schema": {
            "type": "object",
            "properties": {
                "product_specs": {"type": "object"},
                "competitor_insights": {"type": "object"},
                "market": {"type": "string", "default": "amazon-us"},
                "keywords": {"type": "array", "items": {"type": "string"}},
                "complaints": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["product_specs", "competitor_insights"],
        },
    },
]


# ─── Tool handlers ────────────────────────────────────────────────────────────

def handle_crawl_product(inputs: dict) -> dict:
    from app.web_access.fetcher import fetch_page, detect_platform
    platform, content, tool_used = asyncio.run(fetch_page(inputs["url"]))
    return {
        "platform": platform,
        "content": content[:6000],  # cap for context window
        "full_length": len(content),
        "tool_used": tool_used,
    }


def handle_crawl_pages_parallel(inputs: dict) -> dict:
    from app.web_access.fetcher import fetch_pages_parallel
    results = asyncio.run(
        fetch_pages_parallel(inputs["urls"], inputs.get("max_concurrent", 4))
    )
    # Truncate content for context
    for r in results:
        if r.get("content"):
            r["content"] = r["content"][:3000]
    return {"results": results, "count": len(results)}


def handle_search_amazon(inputs: dict) -> dict:
    from app.web_access.fetcher import search_amazon
    candidates = asyncio.run(
        search_amazon(inputs["keyword"], inputs.get("marketplace", "amazon.com"))
    )
    return {"candidates": candidates, "count": len(candidates)}


def handle_search_web(inputs: dict) -> dict:
    from app.web_access.fetcher import search_web
    result = asyncio.run(search_web(inputs["query"]))
    return {"summary": result}


def handle_get_site_experience(inputs: dict) -> dict:
    from app.web_access.site_experience import get_site_experience
    return get_site_experience(inputs["url"]) or {"message": "No experience recorded yet"}


def handle_parse_product(inputs: dict) -> dict:
    from app.services.parser import parse_product_page
    return parse_product_page(inputs["platform"], inputs["content"])


def handle_match_products(inputs: dict) -> dict:
    from app.ai.client import match_products
    return match_products(inputs["source"], inputs["target"])


def handle_analyze_competitors(inputs: dict) -> dict:
    from app.services.analyzer import run_competitor_analysis
    return run_competitor_analysis(inputs["competitors"])


def handle_calculate_margin(inputs: dict) -> dict:
    from app.services.pricing import calculate_margin, CostParams
    cp_raw = inputs["cost_params"]
    cp = CostParams(
        purchase_price=cp_raw.get("purchasePrice", 0),
        domestic_shipping=cp_raw.get("domesticShipping", 0),
        international_shipping=cp_raw.get("internationalShipping", 0),
        fba_fee=cp_raw.get("fbaFee", 0),
        commission_rate=cp_raw.get("commissionRate", 0.15),
        ads_rate=cp_raw.get("adsRate", 0.08),
        tax_rate=cp_raw.get("taxRate", 0.03),
        exchange_rate=cp_raw.get("exchangeRate", 7.2),
    )
    return calculate_margin(cp, inputs["sell_price"])


def handle_generate_listing(inputs: dict) -> dict:
    from app.ai.client import generate_listing
    return generate_listing(
        product_specs=inputs["product_specs"],
        competitor_insights=inputs["competitor_insights"],
        market=inputs.get("market", "amazon-us"),
        keywords=inputs.get("keywords"),
        complaints=inputs.get("complaints"),
    )


TOOL_HANDLERS: dict[str, Callable] = {
    "crawl_product":        handle_crawl_product,
    "crawl_pages_parallel": handle_crawl_pages_parallel,
    "search_amazon":        handle_search_amazon,
    "search_web":           handle_search_web,
    "get_site_experience":  handle_get_site_experience,
    "parse_product":        handle_parse_product,
    "match_products":       handle_match_products,
    "analyze_competitors":  handle_analyze_competitors,
    "calculate_margin":     handle_calculate_margin,
    "generate_listing":     handle_generate_listing,
}


def dispatch(tool_name: str, tool_input: dict) -> dict:
    handler = TOOL_HANDLERS.get(tool_name)
    if not handler:
        return {"error": f"Unknown tool: {tool_name}"}
    try:
        return handler(tool_input)
    except Exception as e:
        return {"error": str(e), "tool": tool_name}
