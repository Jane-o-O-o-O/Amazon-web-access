from datetime import datetime
from sqlalchemy import String, Text, Integer, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class CompetitorReport(Base):
    __tablename__ = "competitor_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    task_id: Mapped[str] = mapped_column(String(50), index=True)
    source_product_id: Mapped[int] = mapped_column(Integer)
    report_json: Mapped[dict | None] = mapped_column(JSON)
    summary_text: Mapped[str | None] = mapped_column(Text)
    pain_points_json: Mapped[list | None] = mapped_column(JSON)
    keywords_json: Mapped[list | None] = mapped_column(JSON)
    differentiation_suggestions: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
