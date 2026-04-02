"""
Listing service: generate Amazon listing copy using Claude.
"""
from app.ai.client import generate_listing


def create_listing(
    product: dict,
    competitor_analysis: dict,
    market: str = "amazon-us",
    tone: str = "professional",
    keyword_focus: list[str] | None = None,
) -> dict:
    """
    Generate a full Amazon listing draft for a product.
    """
    keywords = keyword_focus or competitor_analysis.get("keyword_themes", [])
    complaints = competitor_analysis.get("complaint_topics", [])

    listing = generate_listing(
        product_specs=product,
        competitor_insights=competitor_analysis,
        market=market,
        keywords=keywords,
        complaints=complaints,
    )
    return listing
