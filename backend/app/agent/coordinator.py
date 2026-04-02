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

Your job is to analyze a supply-chain product (from 1688 / Alibaba) and help the seller:
1. Understand the product's specs and positioning
2. Find matching Amazon competitors
3. Analyze the competitive landscape
4. Estimate profit margins
5. Generate an optimized Amazon listing

You have the following tools available. Use them in logical order:
- crawl_product      → fetch the source product page
- parse_product      → extract structured fields from page content
- search_amazon      → search Amazon for matching products
- match_products     → score similarity (call once per top candidate)
- analyze_competitors → summarize competition from top candidates
- calculate_margin   → compute profitability
- generate_listing   → write the Amazon listing copy

Rules:
- Always crawl and parse before searching
- Search with a concise English keyword derived from the product title
- Match at least 3 and at most 5 top candidates
- After all tools complete, write a brief business summary (2-3 sentences)
- If a tool returns an error, note it but continue with available data
- Do NOT fabricate product data
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
