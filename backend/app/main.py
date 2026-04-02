from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import tasks, listings, export

app = FastAPI(
    title=settings.APP_NAME,
    description="Cross-border e-commerce product comparison & Amazon listing generator",
    version="0.1.0",
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


@app.get("/health")
async def health():
    return {"status": "ok", "app": settings.APP_NAME}
