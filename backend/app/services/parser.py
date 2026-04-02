"""
Parser service: extract structured product data from raw page content using Claude.
"""
from app.ai.client import extract_product_info


def parse_product_page(platform: str, raw_content: str) -> dict:
    """
    Parse raw page content into a structured product dict.
    """
    data = extract_product_info(platform, raw_content)
    # Normalise numeric fields
    for field in ("price_min", "price_max", "moq", "package_quantity", "rating", "review_count"):
        val = data.get(field)
        if val is not None:
            try:
                data[field] = float(val) if field in ("price_min", "price_max", "rating") else int(float(val))
            except (TypeError, ValueError):
                data[field] = None
    return data
