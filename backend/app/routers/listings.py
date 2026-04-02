from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.listing import create_listing

router = APIRouter(prefix="/api/listings", tags=["listings"])


class RegenerateRequest(BaseModel):
    productId: str
    market: str = "amazon-us"
    tone: str = "professional"
    keywordFocus: list[str] = []
    productSpecs: dict = {}
    competitorInsights: dict = {}


@router.post("/regenerate")
async def regenerate_listing(body: RegenerateRequest):
    try:
        listing = create_listing(
            product=body.productSpecs,
            competitor_analysis=body.competitorInsights,
            market=body.market,
            tone=body.tone,
            keyword_focus=body.keywordFocus,
        )
        return {"productId": body.productId, "listing": listing}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
