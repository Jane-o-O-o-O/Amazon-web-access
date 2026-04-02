"""
Agent tool definitions.

Each tool is callable by the coordinator agent.
Tools wrap the service layer so the agent can dispatch work without knowing
implementation details.

Tool schema follows Anthropic tool_use format:
  { name, description, input_schema }

Tool handlers are plain sync functions that take a dict and return a dict.
"""
import json
import asyncio
from typing import Callable


# ─── Tool definitions (what the LLM sees) ────────────────────────────────────

TOOL_SCHEMAS = [
    {
        "name": "crawl_product",
        "description": (
            "Fetch a product page (1688 / Alibaba / Amazon) using the best available method "
            "(CDP browser > web_search > httpx). Returns raw text content of the page."
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
        "name": "search_amazon",
        "description": "Search Amazon for products matching a keyword. Returns a list of candidates.",
        "input_schema": {
            "type": "object",
            "properties": {
                "keyword": {"type": "string", "description": "Search keyword (derived from product title)"},
                "marketplace": {
                    "type": "string",
                    "description": "Amazon domain, e.g. amazon.com / amazon.co.uk",
                    "default": "amazon.com",
                },
            },
            "required": ["keyword"],
        },
    },
    {
        "name": "parse_product",
        "description": "Parse raw page content into structured product fields using Claude.",
        "input_schema": {
            "type": "object",
            "properties": {
                "platform": {"type": "string", "description": "1688 | alibaba | amazon | unknown"},
                "content": {"type": "string", "description": "Raw page text"},
            },
            "required": ["platform", "content"],
        },
    },
    {
        "name": "match_products",
        "description": "Score similarity between a source product and an Amazon candidate. Returns match_score 0-100.",
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
        "description": "Generate an Amazon listing (title, bullets, description, search terms) from product info and competitor insights.",
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
    from app.services.crawler import crawl_product_page
    platform, content = asyncio.run(crawl_product_page(inputs["url"]))
    return {"platform": platform, "content": content, "length": len(content)}


def handle_search_amazon(inputs: dict) -> dict:
    from app.services.crawler import search_amazon_candidates
    candidates = asyncio.run(
        search_amazon_candidates(inputs["keyword"], inputs.get("marketplace", "amazon.com"))
    )
    return {"candidates": candidates, "count": len(candidates)}


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
    "crawl_product":      handle_crawl_product,
    "search_amazon":      handle_search_amazon,
    "parse_product":      handle_parse_product,
    "match_products":     handle_match_products,
    "analyze_competitors": handle_analyze_competitors,
    "calculate_margin":   handle_calculate_margin,
    "generate_listing":   handle_generate_listing,
}


def dispatch(tool_name: str, tool_input: dict) -> dict:
    """Dispatch a tool call to its handler. Returns result dict."""
    handler = TOOL_HANDLERS.get(tool_name)
    if not handler:
        return {"error": f"Unknown tool: {tool_name}"}
    try:
        return handler(tool_input)
    except Exception as e:
        return {"error": str(e), "tool": tool_name}
