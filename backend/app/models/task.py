from datetime import datetime
from sqlalchemy import String, Text, Integer, DateTime, JSON, Float
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class AnalysisTask(Base):
    __tablename__ = "analysis_tasks"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)  # task_xxx
    status: Mapped[str] = mapped_column(String(20), default="queued")  # queued|running|done|failed
    stage: Mapped[str | None] = mapped_column(String(50))  # crawling|parsing|matching|analyzing|generating
    progress: Mapped[int] = mapped_column(Integer, default=0)  # 0-100
    source_url: Mapped[str] = mapped_column(Text)
    target_marketplace: Mapped[str] = mapped_column(String(50), default="amazon-us")
    cost_params: Mapped[dict | None] = mapped_column(JSON)
    source_product_id: Mapped[int | None] = mapped_column(Integer)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
