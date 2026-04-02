from datetime import datetime
from sqlalchemy import String, Text, Float, Integer, DateTime, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class ProductRaw(Base):
    __tablename__ = "products_raw"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source_platform: Mapped[str] = mapped_column(String(50))  # 1688 | alibaba | amazon
    source_url: Mapped[str] = mapped_column(Text, unique=True, index=True)
    source_id: Mapped[str | None] = mapped_column(String(200))
    raw_html_path: Mapped[str | None] = mapped_column(Text)
    raw_json: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    normalized: Mapped["ProductNormalized | None"] = relationship(back_populates="raw")


class ProductNormalized(Base):
    __tablename__ = "products_normalized"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    raw_product_id: Mapped[int] = mapped_column(ForeignKey("products_raw.id"))
    platform: Mapped[str] = mapped_column(String(50))
    title: Mapped[str | None] = mapped_column(Text)
    brand: Mapped[str | None] = mapped_column(String(200))
    category: Mapped[str | None] = mapped_column(String(200))
    price_min: Mapped[float | None] = mapped_column(Float)
    price_max: Mapped[float | None] = mapped_column(Float)
    currency: Mapped[str | None] = mapped_column(String(10))
    moq: Mapped[int | None] = mapped_column(Integer)
    material: Mapped[str | None] = mapped_column(Text)
    size: Mapped[str | None] = mapped_column(Text)
    color: Mapped[str | None] = mapped_column(Text)
    package_quantity: Mapped[int | None] = mapped_column(Integer)
    attributes_json: Mapped[dict | None] = mapped_column(JSON)
    images_json: Mapped[list | None] = mapped_column(JSON)
    rating: Mapped[float | None] = mapped_column(Float)
    review_count: Mapped[int | None] = mapped_column(Integer)
    seller_name: Mapped[str | None] = mapped_column(String(300))
    ship_from: Mapped[str | None] = mapped_column(String(200))
    normalized_text: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    raw: Mapped["ProductRaw"] = relationship(back_populates="normalized")
