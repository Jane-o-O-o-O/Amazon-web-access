"""
Background tasks using Celery + Redis.
"""
import uuid
from celery import Celery
from app.config import settings

celery_app = Celery(
    "crossborder",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)
celery_app.conf.task_serializer = "json"
celery_app.conf.result_serializer = "json"


@celery_app.task(bind=True, name="tasks.run_product_analysis")
def run_product_analysis(self, task_id: str, source_url: str, cost_params: dict, marketplace: str):
    """
    Full pipeline: crawl → parse → search → match → analyze → price → listing
    Updates task progress in Redis along the way.
    """
    import redis
    import json

    r = redis.from_url(settings.REDIS_URL)

    def set_progress(stage: str, progress: int):
        r.set(
            f"task:{task_id}:progress",
            json.dumps({"stage": stage, "progress": progress}),
            ex=3600,
        )

    try:
        from app.services.crawler import crawl_product_page, search_amazon_candidates
        from app.services.parser import parse_product_page
        from app.services.matcher import rank_candidates
        from app.services.analyzer import run_competitor_analysis
        from app.services.pricing import calculate_margin, CostParams
        from app.services.listing import create_listing
        import asyncio

        set_progress("crawling", 5)

        # 1. Crawl source product
        platform, content = asyncio.run(crawl_product_page(source_url))
        set_progress("parsing", 20)

        # 2. Parse product info
        product = parse_product_page(platform, content)
        product["source_url"] = source_url
        product["platform"] = platform
        set_progress("searching", 35)

        # 3. Search Amazon for candidates
        keyword = product.get("title", "")[:100]
        candidates = asyncio.run(search_amazon_candidates(keyword))
        set_progress("matching", 50)

        # 4. Match & rank candidates
        ranked = rank_candidates(product, candidates[:10])
        top_candidates = ranked[:5]
        set_progress("analyzing", 65)

        # 5. Competitor analysis
        competitor_products = [m["candidate"] for m in top_candidates]
        competitor_analysis = run_competitor_analysis(competitor_products)
        set_progress("pricing", 80)

        # 6. Profit calculation (use sell_price from top competitor if available)
        sell_price = 0.0
        if top_candidates:
            try:
                sell_price = float(top_candidates[0]["candidate"].get("price", 0) or 0)
            except (TypeError, ValueError):
                sell_price = 0.0

        cp = CostParams(
            purchase_price=cost_params.get("purchasePrice", 0),
            domestic_shipping=cost_params.get("domesticShipping", 0),
            international_shipping=cost_params.get("internationalShipping", 0),
            fba_fee=cost_params.get("fbaFee", 0),
            commission_rate=cost_params.get("commissionRate", 0.15),
            ads_rate=cost_params.get("adsRate", 0.08),
            tax_rate=cost_params.get("taxRate", 0.03),
            exchange_rate=cost_params.get("exchangeRate", 7.2),
        )
        margin = calculate_margin(cp, sell_price or cp.purchase_price / cp.exchange_rate * 3)
        set_progress("generating", 90)

        # 7. Generate listing
        listing = create_listing(product, competitor_analysis)
        set_progress("done", 100)

        result = {
            "task_id": task_id,
            "status": "done",
            "source_product": product,
            "candidates": top_candidates,
            "competitor_analysis": competitor_analysis,
            "margin": margin,
            "listing": listing,
        }
        r.set(f"task:{task_id}:result", json.dumps(result, ensure_ascii=False), ex=86400)
        r.set(f"task:{task_id}:status", "done", ex=86400)
        return result

    except Exception as e:
        r.set(f"task:{task_id}:status", "failed", ex=86400)
        r.set(f"task:{task_id}:error", str(e), ex=86400)
        raise
