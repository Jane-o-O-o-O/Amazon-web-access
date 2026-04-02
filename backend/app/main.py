from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import tasks, listings, export, settings as settings_router

app = FastAPI(
    title=settings.APP_NAME,
    description="Cross-border e-commerce product comparison & Amazon listing generator",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tasks.router)
app.include_router(listings.router)
app.include_router(export.router)
app.include_router(settings_router.router)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "model_provider": settings.MODEL_PROVIDER,
        "model": settings.MODEL_NAME,
        "cdp_enabled": settings.CDP_ENABLED,
    }
