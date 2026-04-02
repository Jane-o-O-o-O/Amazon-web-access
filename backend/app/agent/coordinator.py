"""
Coordinator — high-level entry point for the product analysis Agent.

Responsibilities:
  1. Build the system prompt that tells Claude its role and available tools
  2. Build the user message from task inputs
  3. Run the agent loop
  4. Map raw tool_results → the structured TaskResult schema
"""
from app.agent.loop import run_agent_loop


SYSTEM_PROMPT = """You are CrossBorder AI Copilot — a specialist agent for cross-border e-commerce sellers.

Your job: analyze a supply-chain product (1688 / Alibaba) → find Amazon competitors → analyze market → estimate profit → generate listing.

## Available tools

### Web access (use these first)
- get_site_experience   → check known patterns for a domain BEFORE crawling
- crawl_product         → fetch a single page (auto-selects CDP > Jina > web_fetch > curl)
- crawl_pages_parallel  → fetch multiple pages concurrently (use for Amazon candidate pages)
- search_amazon         → search Amazon for matching products (CDP or web_search)
- search_web            → general web search

### Analysis & generation
- parse_product         → extract structured fields from page content via LLM
- match_products        → score similarity between source and Amazon candidate (0-100)
- analyze_competitors   → generate competitor analysis report from multiple products
- calculate_margin      → compute profit margins
- generate_listing      → write Amazon listing copy

## Recommended workflow

1. get_site_experience(source_url) — learn how to crawl the site
2. crawl_product(source_url) — fetch the product page
3. parse_product(platform, content) — extract structured data
4. search_amazon(keyword) — find Amazon candidates
5. crawl_pages_parallel(top_candidate_urls) — fetch candidate detail pages (parallel!)
6. match_products(source, candidate) × 3-5 times — score each candidate
7. analyze_competitors(top_candidates) — market analysis
8. calculate_margin(cost_params, sell_price) — profit
9. generate_listing(product, insights) — write the listing

## Rules
- Always check site experience before crawling
- Use crawl_pages_parallel when fetching multiple Amazon pages — much faster
- Search keyword must be concise English (derived from product title, ≤6 words)
- Match 3-5 top candidates
- If a tool errors, note it and continue with available data
- Never fabricate product specs, prices, or certifications
- End with a 2-3 sentence business summary
"""


def build_user_message(source_url: str, cost_params: dict, marketplace: str = "amazon-us") -> str:
    import json
    return (
        f"Please analyze this product: {source_url}\n\n"
        f"Target marketplace: {marketplace}\n"
        f"Cost parameters: {json.dumps(cost_params, ensure_ascii=False)}\n\n"
        "Complete the full analysis: crawl → parse → search Amazon → match → "
        "analyze competitors → calculate margin → generate listing."
    )


def run_analysis(
    source_url: str,
    cost_params: dict,
    marketplace: str = "amazon-us",
    progress_callback=None,
    provider: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    model: str | None = None,
) -> dict:
    """
    Run the full product analysis via the Agent loop.

    Returns a dict matching TaskResult schema:
      {
        source_product, candidates, competitor_analysis,
        margin, listing, agent_summary
      }
    """
    user_msg = build_user_message(source_url, cost_params, marketplace)

    result = run_agent_loop(
        system_prompt=SYSTEM_PROMPT,
        user_message=user_msg,
        progress_callback=progress_callback,
        provider=provider,
        api_key=api_key,
        base_url=base_url,
        model=model,
    )

    tr = result["tool_results"]

    # ── Map tool results → output schema ──────────────────────────────────────
    source_product = tr.get("parse_product", {})
    source_product["source_url"] = source_url
    source_product["platform"] = tr.get("crawl_product", {}).get("platform", "unknown")

    candidates_raw = tr.get("search_amazon", {}).get("candidates", [])

    # match_products may have been called multiple times — collect last N
    # (in practice the agent calls it per candidate; we keep whatever came back)
    match_results = tr.get("match_products")
    if isinstance(match_results, list):
        candidates = match_results
    elif isinstance(match_results, dict):
        candidates = [match_results]
    else:
        # Build lightweight candidates from raw search results
        candidates = [{"candidate": c, "match_score": 0, "match_level": "unknown"} for c in candidates_raw[:5]]

    return {
        "source_product":     source_product,
        "candidates":         candidates,
        "competitor_analysis": tr.get("analyze_competitors", {}),
        "margin":             tr.get("calculate_margin", {}),
        "listing":            tr.get("generate_listing", {}),
        "agent_summary":      result.get("final_text", ""),
    }
