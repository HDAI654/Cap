from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.persistence.models.base import Base


class OrderHistoryModel(Base):
    __tablename__ = "order_history"

    entry_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    order_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    trader_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    instrument_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    side: Mapped[str | None] = mapped_column(String(8), nullable=True)
    order_type: Mapped[str | None] = mapped_column(String(16), nullable=True)
    quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    filled_quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    remaining_quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    price: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    price_currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
