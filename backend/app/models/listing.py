from datetime import datetime
from sqlalchemy import String, Text, Integer, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class ListingDraft(Base):
    __tablename__ = "listing_drafts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    task_id: Mapped[str] = mapped_column(String(50), index=True)
    product_id: Mapped[int] = mapped_column(Integer)
    market: Mapped[str] = mapped_column(String(50), default="amazon-us")
    language: Mapped[str] = mapped_column(String(10), default="en")
    title: Mapped[str | None] = mapped_column(Text)
    bullets_json: Mapped[list | None] = mapped_column(JSON)  # list of bullet strings
    description: Mapped[str | None] = mapped_column(Text)
    search_terms: Mapped[str | None] = mapped_column(Text)
    image_copy_json: Mapped[list | None] = mapped_column(JSON)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
