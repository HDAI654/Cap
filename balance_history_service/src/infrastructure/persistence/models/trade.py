from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.persistence.models.base import Base


class TradeModel(Base):
    __tablename__ = "trades"

    trade_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    maker_order_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    taker_order_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    buyer_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    seller_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    instrument_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    execution_price: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    execution_price_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    executed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
