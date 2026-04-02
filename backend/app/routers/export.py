import io
import json
import redis as redis_lib
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import pandas as pd
from app.config import settings

router = APIRouter(prefix="/api/export", tags=["export"])
r = redis_lib.from_url(settings.REDIS_URL)


@router.get("/tasks/{task_id}/csv")
async def export_task_csv(task_id: str):
    result_raw = r.get(f"task:{task_id}:result")
    if not result_raw:
        raise HTTPException(status_code=404, detail="Result not found or task incomplete")
    result = json.loads(result_raw)

    rows = []
    source = result.get("source_product", {})
    for match in result.get("candidates", []):
        candidate = match.get("candidate", {})
        margin = result.get("margin", {})
        rows.append({
            "Source Title": source.get("title", ""),
            "Source Price (CNY)": source.get("price_min", ""),
            "Amazon Title": candidate.get("title", ""),
            "Amazon Price (USD)": candidate.get("price", ""),
            "Amazon Rating": candidate.get("rating", ""),
            "Amazon Reviews": candidate.get("review_count", ""),
            "Match Score": match.get("match_score", ""),
            "Match Level": match.get("match_level", ""),
            "Net Margin": margin.get("net_margin", ""),
            "Suggested Price Min": margin.get("suggested_price_min", ""),
            "Suggested Price Max": margin.get("suggested_price_max", ""),
        })

    df = pd.DataFrame(rows)
    buf = io.BytesIO()
    df.to_csv(buf, index=False)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=task_{task_id}_result.csv"},
    )


@router.get("/tasks/{task_id}/json")
async def export_task_json(task_id: str):
    result_raw = r.get(f"task:{task_id}:result")
    if not result_raw:
        raise HTTPException(status_code=404, detail="Result not found or task incomplete")
    result = json.loads(result_raw)
    buf = io.BytesIO(json.dumps(result, ensure_ascii=False, indent=2).encode())
    return StreamingResponse(
        buf,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=task_{task_id}_result.json"},
    )
