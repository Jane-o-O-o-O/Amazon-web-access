from datetime import datetime
from sqlalchemy import String, Text, Integer, DateTime, Float
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class MarginCalculation(Base):
    __tablename__ = "margin_calculations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    task_id: Mapped[str] = mapped_column(String(50), index=True)
    product_id: Mapped[int] = mapped_column(Integer)
    cost_purchase: Mapped[float] = mapped_column(Float)
    domestic_shipping: Mapped[float] = mapped_column(Float, default=0.0)
    international_shipping: Mapped[float] = mapped_column(Float, default=0.0)
    fba_fee: Mapped[float] = mapped_column(Float, default=0.0)
    commission_fee: Mapped[float] = mapped_column(Float, default=0.0)
    ads_cost: Mapped[float] = mapped_column(Float, default=0.0)
    tax_cost: Mapped[float] = mapped_column(Float, default=0.0)
    exchange_rate: Mapped[float] = mapped_column(Float, default=7.2)
    sell_price: Mapped[float] = mapped_column(Float)
    total_cost: Mapped[float] = mapped_column(Float)
    gross_profit: Mapped[float] = mapped_column(Float)
    net_profit: Mapped[float] = mapped_column(Float)
    gross_margin: Mapped[float] = mapped_column(Float)
    net_margin: Mapped[float] = mapped_column(Float)
    suggested_price_min: Mapped[float | None] = mapped_column(Float)
    suggested_price_max: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
