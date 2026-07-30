from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


class CashBalanceResponse(BaseModel):
    """Cash balance projection."""

    model_config = ConfigDict(from_attributes=True)

    currency: str
    available: Decimal
    reserved: Decimal


class HoldingResponse(BaseModel):
    """Holding projection."""

    model_config = ConfigDict(from_attributes=True)

    instrument_id: str
    available: int
    reserved: int
    average_cost: Decimal
    average_cost_currency: str


class WalletResponse(BaseModel):
    """Full wallet projection returned by GET."""

    model_config = ConfigDict(from_attributes=True)

    wallet_id: str
    trader_id: str
    status: str
    cash_balances: list[CashBalanceResponse] = Field(default_factory=list)
    holdings: list[HoldingResponse] = Field(default_factory=list)


class CreateWalletResponse(BaseModel):
    """Response after creating a wallet."""

    wallet_id: str


class ErrorResponse(BaseModel):
    """Standard error body."""

    detail: str
