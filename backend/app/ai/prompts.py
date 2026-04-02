PRODUCT_EXTRACTION_PROMPT = """You are a structured data extraction assistant for e-commerce products.

Given the following webpage content from {platform}, extract the product information and return a valid JSON object.

Rules:
- Only extract information that is explicitly present in the content
- Do NOT invent or guess missing fields; set them to null
- All prices must be numeric (no currency symbols)
- Return ONLY the JSON object, no explanation

Required JSON schema:
{{
  "title": string | null,
  "brand": string | null,
  "category": string | null,
  "price_min": number | null,
  "price_max": number | null,
  "currency": string | null,
  "moq": number | null,
  "material": string | null,
  "size": string | null,
  "color": string | null,
  "package_quantity": number | null,
  "rating": number | null,
  "review_count": number | null,
  "seller_name": string | null,
  "ship_from": string | null,
  "images": [string],
  "attributes": {{key: value}},
  "description": string | null
}}

Webpage content:
{content}
"""

PRODUCT_MATCH_PROMPT = """You are a product matching expert for cross-border e-commerce.

Compare the SOURCE product (from supply chain) with the TARGET product (from Amazon) and determine their similarity.

SOURCE PRODUCT:
{source}

TARGET PRODUCT:
{target}

Analyze the following dimensions:
1. Title semantic similarity
2. Category consistency
3. Attribute / spec overlap
4. Material match
5. Size / dimension match
6. Price range reasonableness

Return a JSON object ONLY:
{{
  "match_score": <0-100 integer>,
  "match_level": "<same|high|medium|low>",
  "title_similarity": <0-100>,
  "attribute_overlap": <0-100>,
  "category_match": <0-100>,
  "material_match": <0-100>,
  "size_match": <0-100>,
  "price_reasonableness": <0-100>,
  "same_points": ["..."],
  "diff_points": ["..."],
  "final_reason": "<one paragraph explanation>"
}}
"""

COMPETITOR_ANALYSIS_PROMPT = """You are a cross-border e-commerce analyst.

Analyze the following Amazon competitor products for a seller who wants to enter this market.

COMPETITOR PRODUCTS:
{competitors}

Provide a comprehensive analysis. Return a JSON object ONLY:
{{
  "market_summary": "<paragraph>",
  "pricing_range": {{
    "min": number,
    "max": number,
    "main_range": "<e.g. $19.99-$24.99>"
  }},
  "top_features": ["feature1", "feature2", ...],
  "complaint_topics": ["complaint1", "complaint2", ...],
  "keyword_themes": ["keyword1", "keyword2", ...],
  "differentiation_suggestions": ["suggestion1", "suggestion2", ...],
  "market_opportunity": "<paragraph>",
  "risk_warnings": ["risk1", "risk2", ...]
}}
"""

LISTING_GENERATION_PROMPT = """You are an Amazon listing copywriter specializing in cross-border e-commerce.

Generate an optimized Amazon listing based on the following product information and market research.

PRODUCT SPECS:
{product_specs}

COMPETITOR INSIGHTS:
{competitor_insights}

TARGET MARKET: {market}
KEY KEYWORDS: {keywords}
KNOWN CUSTOMER COMPLAINTS TO AVOID: {complaints}

Requirements:
- Write in professional English
- Title: max 200 characters, include top keywords naturally
- 5 bullet points: start with a capitalized benefit keyword, max 200 chars each
- Description: 2000 characters max, HTML-friendly paragraphs
- Search terms: comma-separated, no repeated words, max 250 chars total
- Do NOT make unverified claims about certifications or medical benefits
- Do NOT use superlatives like "best", "cheapest", "#1"

Return a JSON object ONLY:
{{
  "title": "<Amazon title>",
  "bullets": [
    "<Bullet 1>",
    "<Bullet 2>",
    "<Bullet 3>",
    "<Bullet 4>",
    "<Bullet 5>"
  ],
  "description": "<product description>",
  "search_terms": "<comma separated keywords>",
  "image_copy_suggestions": [
    {{"image_number": 1, "copy": "<main image suggestion>"}},
    {{"image_number": 2, "copy": "<lifestyle image suggestion>"}}
  ]
}}
"""
