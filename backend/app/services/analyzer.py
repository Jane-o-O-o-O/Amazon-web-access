"""
Analyzer service: generate competitor analysis from matched Amazon products.
"""
from app.ai.client import analyze_competitors


def run_competitor_analysis(competitor_products: list[dict]) -> dict:
    """
    Generate a structured competitor analysis report from a list of Amazon products.
    """
    if not competitor_products:
        return {
            "market_summary": "No competitor data available.",
            "pricing_range": {},
            "top_features": [],
            "complaint_topics": [],
            "keyword_themes": [],
            "differentiation_suggestions": [],
            "market_opportunity": "",
            "risk_warnings": [],
        }
    return analyze_competitors(competitor_products)
