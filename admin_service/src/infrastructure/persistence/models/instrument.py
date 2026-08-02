from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.persistence.models.base import Base


class InstrumentModel(Base):
    __tablename__ = "instruments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    symbol: Mapped[str] = mapped_column(
        String(32), nullable=False, unique=True, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    tick_size: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    tick_size_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    lot_size: Mapped[int] = mapped_column(Integer, nullable=False)
    minimum_order_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    maximum_order_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    total_shares: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
