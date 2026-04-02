from datetime import datetime
from sqlalchemy import String, Text, Integer, DateTime, JSON, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class ProductMatch(Base):
    __tablename__ = "product_matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    task_id: Mapped[str] = mapped_column(String(50), index=True)
    source_product_id: Mapped[int] = mapped_column(Integer)
    target_product_id: Mapped[int] = mapped_column(Integer)
    match_score: Mapped[float] = mapped_column(Float)
    match_level: Mapped[str] = mapped_column(String(20))  # same|high|medium|low
    similarity_breakdown: Mapped[dict | None] = mapped_column(JSON)
    match_reason: Mapped[str | None] = mapped_column(Text)
    diff_summary: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
