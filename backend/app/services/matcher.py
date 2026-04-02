"""
Matcher service: score similarity between source and Amazon candidate products.
"""
from app.ai.client import match_products


def score_match(source_product: dict, target_product: dict) -> dict:
    """
    Score the match between source and target product.
    Returns a match result dict with score, level, reasons.
    """
    result = match_products(source_product, target_product)
    score = result.get("match_score", 0)
    # Derive level from score if LLM didn't provide it
    if "match_level" not in result:
        if score >= 85:
            result["match_level"] = "same"
        elif score >= 65:
            result["match_level"] = "high"
        elif score >= 40:
            result["match_level"] = "medium"
        else:
            result["match_level"] = "low"
    return result


def rank_candidates(source_product: dict, candidates: list[dict]) -> list[dict]:
    """
    Score and rank all candidates. Returns list sorted by match_score descending.
    """
    results = []
    for candidate in candidates:
        try:
            match = score_match(source_product, candidate)
            match["candidate"] = candidate
            results.append(match)
        except Exception as e:
            results.append({
                "match_score": 0,
                "match_level": "low",
                "error": str(e),
                "candidate": candidate,
            })
    results.sort(key=lambda x: x.get("match_score", 0), reverse=True)
    return results
