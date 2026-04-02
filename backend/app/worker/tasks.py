"""
Background tasks using Celery + Redis.

Uses the Agent coordinator (coordinator.py) which runs the full
tool-use loop via Claude. Falls back to sequential services for
non-Anthropic providers.
"""
import json
import redis as redis_lib
from celery import Celery
from app.config import settings

celery_app = Celery(
    "crossborder",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)
celery_app.conf.task_serializer = "json"
celery_app.conf.result_serializer = "json"


def _set_progress(r: redis_lib.Redis, task_id: str, stage: str, progress: int):
    r.set(
        f"task:{task_id}:progress",
        json.dumps({"stage": stage, "progress": progress}),
        ex=3600,
    )


@celery_app.task(bind=True, name="tasks.run_product_analysis")
def run_product_analysis(
    self,
    task_id: str,
    source_url: str,
    cost_params: dict,
    marketplace: str,
    # Optional model override (from frontend settings)
    provider: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    model: str | None = None,
):
    """
    Full analysis pipeline via the Agent coordinator.
    Progress is written to Redis so the frontend can poll it.
    """
    r = redis_lib.from_url(settings.REDIS_URL)

    def progress(stage: str, pct: int):
        r.set(f"task:{task_id}:status", "running", ex=86400)
        _set_progress(r, task_id, stage, pct)

    try:
        _set_progress(r, task_id, "starting", 2)

        from app.agent.coordinator import run_analysis

        result = run_analysis(
            source_url=source_url,
            cost_params=cost_params,
            marketplace=marketplace,
            progress_callback=progress,
            provider=provider,
            api_key=api_key,
            base_url=base_url,
            model=model,
        )

        result["task_id"] = task_id
        result["status"] = "done"

        r.set(f"task:{task_id}:result", json.dumps(result, ensure_ascii=False), ex=86400)
        r.set(f"task:{task_id}:status", "done", ex=86400)
        _set_progress(r, task_id, "done", 100)
        return result

    except Exception as e:
        r.set(f"task:{task_id}:status", "failed", ex=86400)
        r.set(f"task:{task_id}:error", str(e), ex=86400)
        _set_progress(r, task_id, "failed", 0)
        raise
