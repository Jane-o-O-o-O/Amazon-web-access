import uuid
import json
import redis as redis_lib
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, HttpUrl
from app.config import settings
from app.worker.tasks import run_product_analysis

router = APIRouter(prefix="/api/tasks", tags=["tasks"])
r = redis_lib.from_url(settings.REDIS_URL)


class CostParams(BaseModel):
    purchasePrice: float = 0.0
    domesticShipping: float = 0.0
    internationalShipping: float = 1.0
    fbaFee: float = 3.2
    commissionRate: float = 0.15
    adsRate: float = 0.08
    taxRate: float = 0.03
    exchangeRate: float = 7.2


class ModelOverride(BaseModel):
    """Optional per-request model configuration. Overrides global settings."""
    provider: str | None = None    # "anthropic" | "openai"
    baseUrl: str | None = None     # e.g. "https://api.deepseek.com/v1"
    apiKey: str | None = None      # if empty, uses global setting
    modelName: str | None = None   # e.g. "deepseek-chat"


class CreateTaskRequest(BaseModel):
    sourceUrl: str
    targetMarketplace: str = "amazon-us"
    cost: CostParams = CostParams()
    modelOverride: ModelOverride | None = None  # optional per-task model


@router.post("/product-analysis")
async def create_product_analysis_task(body: CreateTaskRequest):
    task_id = f"task_{uuid.uuid4().hex[:12]}"
    r.set(f"task:{task_id}:status", "queued", ex=86400)
    r.set(
        f"task:{task_id}:progress",
        json.dumps({"stage": "queued", "progress": 0}),
        ex=86400,
    )
    r.set(f"task:{task_id}:source_url", body.sourceUrl, ex=86400)

    # Resolve model settings: per-request override > Redis stored settings > env defaults
    from app.routers.settings import get_model_settings
    ms = get_model_settings()
    ov = body.modelOverride or ModelOverride()

    run_product_analysis.apply_async(
        args=[task_id, body.sourceUrl, body.cost.model_dump(), body.targetMarketplace],
        kwargs={
            "provider":  ov.provider  or ms.provider,
            "api_key":   ov.apiKey    or ms.api_key,
            "base_url":  ov.baseUrl   or ms.base_url,
            "model":     ov.modelName or ms.model_name,
        },
        task_id=task_id,
    )
    return {"taskId": task_id, "status": "queued"}


@router.get("/{task_id}")
async def get_task_status(task_id: str):
    status = r.get(f"task:{task_id}:status")
    if status is None:
        raise HTTPException(status_code=404, detail="Task not found")
    status = status.decode()
    progress_raw = r.get(f"task:{task_id}:progress")
    progress_data = json.loads(progress_raw) if progress_raw else {"stage": status, "progress": 0}
    error = r.get(f"task:{task_id}:error")
    return {
        "taskId": task_id,
        "status": status,
        "progress": progress_data.get("progress", 0),
        "stage": progress_data.get("stage", status),
        "error": error.decode() if error else None,
    }


@router.get("/{task_id}/result")
async def get_task_result(task_id: str):
    status = r.get(f"task:{task_id}:status")
    if status is None:
        raise HTTPException(status_code=404, detail="Task not found")
    status = status.decode()
    if status != "done":
        raise HTTPException(status_code=202, detail=f"Task not complete. Status: {status}")
    result_raw = r.get(f"task:{task_id}:result")
    if not result_raw:
        raise HTTPException(status_code=404, detail="Result not found")
    return json.loads(result_raw)
