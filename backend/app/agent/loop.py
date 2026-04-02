"""
Agent loop — agentic tool-use loop based on claude-code coordinator pattern.

Flow:
  1. Send coordinator prompt + tools to Claude
  2. Claude returns tool_use blocks → dispatch each tool
  3. Feed tool results back as tool_result blocks
  4. Repeat until Claude returns stop_reason == "end_turn" (no more tools)
  5. Return final text + accumulated results

This mirrors the coordinator → worker pattern from claude-code:
  - Coordinator (Claude) decides WHAT to do and in what order
  - Workers (tool handlers) actually do the work
  - Results flow back as tool_result messages
  - Claude synthesizes a final answer
"""
import json
import anthropic
from app.config import settings
from app.agent.tools import TOOL_SCHEMAS, dispatch


MAX_ITERATIONS = 20  # safety cap on tool rounds


def run_agent_loop(
    system_prompt: str,
    user_message: str,
    progress_callback=None,          # optional: fn(stage: str, pct: int)
    provider: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    model: str | None = None,
) -> dict:
    """
    Run the full agentic loop.

    Returns:
      {
        "final_text": str,          # Claude's final synthesis
        "tool_results": {           # accumulated results by tool name
          "crawl_product": {...},
          "parse_product": {...},
          ...
        }
      }
    """
    p = provider or settings.MODEL_PROVIDER
    m = model or settings.MODEL_NAME
    key = api_key or settings.MODEL_API_KEY

    if p == "anthropic":
        client = anthropic.Anthropic(
            api_key=key,
            base_url=base_url or settings.MODEL_BASE_URL,
        )
    else:
        # For OpenAI-compat providers, fall back to sequential service calls
        # (tool_use loop requires Anthropic format)
        return _run_sequential_fallback(user_message, progress_callback)

    messages = [{"role": "user", "content": user_message}]
    accumulated = {}

    for iteration in range(MAX_ITERATIONS):
        response = client.messages.create(
            model=m,
            max_tokens=4096,
            system=system_prompt,
            tools=TOOL_SCHEMAS,
            messages=messages,
        )

        # Collect text blocks for final answer
        text_parts = []
        tool_calls = []

        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                tool_calls.append(block)

        if not tool_calls:
            # No more tools — done
            return {
                "final_text": "\n".join(text_parts),
                "tool_results": accumulated,
            }

        # Dispatch all tool calls and collect results
        tool_results = []
        for tc in tool_calls:
            if progress_callback:
                _report_progress(tc.name, progress_callback)

            result = dispatch(tc.name, tc.input)
            accumulated[tc.name] = result  # store latest result per tool

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tc.id,
                "content": json.dumps(result, ensure_ascii=False),
            })

        # Append assistant turn + tool results to messages
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})

    return {
        "final_text": "Max iterations reached.",
        "tool_results": accumulated,
    }


def _report_progress(tool_name: str, cb):
    stage_map = {
        "crawl_product":      ("crawling",   15),
        "parse_product":      ("parsing",    30),
        "search_amazon":      ("searching",  45),
        "match_products":     ("matching",   60),
        "analyze_competitors":("analyzing",  75),
        "calculate_margin":   ("pricing",    85),
        "generate_listing":   ("generating", 95),
    }
    stage, pct = stage_map.get(tool_name, ("running", 50))
    cb(stage, pct)


def _run_sequential_fallback(user_message: str, progress_callback=None) -> dict:
    """
    For non-Anthropic providers that don't support tool_use format.
    Extracts URL from message and runs the standard sequential pipeline.
    """
    import re
    from app.services.crawler import crawl_product_page, search_amazon_candidates
    from app.services.parser import parse_product_page
    from app.services.matcher import rank_candidates
    from app.services.analyzer import run_competitor_analysis
    from app.services.pricing import calculate_margin, CostParams
    from app.services.listing import create_listing
    import asyncio

    url_match = re.search(r"https?://\S+", user_message)
    url = url_match.group() if url_match else ""

    def prog(s, p):
        if progress_callback:
            progress_callback(s, p)

    prog("crawling", 10)
    platform, content = asyncio.run(crawl_product_page(url))

    prog("parsing", 25)
    product = parse_product_page(platform, content)
    product["source_url"] = url
    product["platform"] = platform

    prog("searching", 40)
    candidates = asyncio.run(search_amazon_candidates(product.get("title", "")[:80]))

    prog("matching", 55)
    ranked = rank_candidates(product, candidates[:10])

    prog("analyzing", 70)
    competitor_products = [m["candidate"] for m in ranked[:5]]
    competitor_analysis = run_competitor_analysis(competitor_products)

    sell_price = 0.0
    if ranked:
        try:
            sell_price = float(ranked[0]["candidate"].get("price", 0) or 0)
        except (TypeError, ValueError):
            pass

    prog("pricing", 82)
    margin = calculate_margin(CostParams(purchase_price=5.0), sell_price or 15.0)

    prog("generating", 92)
    listing = create_listing(product, competitor_analysis)

    return {
        "final_text": "Analysis complete.",
        "tool_results": {
            "crawl_product":      {"platform": platform, "content": content[:500]},
            "parse_product":      product,
            "search_amazon":      {"candidates": candidates},
            "match_products":     ranked,
            "analyze_competitors": competitor_analysis,
            "calculate_margin":   margin,
            "generate_listing":   listing,
        },
    }
