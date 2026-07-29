from decimal import Decimal
from sqlalchemy import (
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.infrastructure.persistence.models.base import Base


class WalletModel(Base):
    __tablename__ = "wallets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    trader_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False)

    cash_balances: Mapped[list["CashBalanceModel"]] = relationship(
        back_populates="wallet",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    holdings: Mapped[list["HoldingModel"]] = relationship(
        back_populates="wallet",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class CashBalanceModel(Base):
    __tablename__ = "cash_balances"
    __table_args__ = (
        UniqueConstraint(
            "wallet_id", "currency", name="uq_cash_balance_wallet_currency"
        ),
    )

    wallet_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("wallets.id", ondelete="CASCADE"),
        primary_key=True,
    )
    currency: Mapped[str] = mapped_column(String(3), primary_key=True)
    available: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    reserved: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)

    wallet: Mapped["WalletModel"] = relationship(back_populates="cash_balances")


class HoldingModel(Base):
    __tablename__ = "holdings"
    __table_args__ = (
        UniqueConstraint(
            "wallet_id",
            "instrument_id",
            name="uq_holding_wallet_instrument",
        ),
    )

    wallet_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("wallets.id", ondelete="CASCADE"),
        primary_key=True,
    )
    instrument_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    available: Mapped[int] = mapped_column(Integer, nullable=False)
    reserved: Mapped[int] = mapped_column(Integer, nullable=False)
    average_cost: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    average_cost_currency: Mapped[str] = mapped_column(String(3), nullable=False)

    wallet: Mapped["WalletModel"] = relationship(back_populates="holdings")
