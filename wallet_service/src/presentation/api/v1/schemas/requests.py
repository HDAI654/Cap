from decimal import Decimal
from pydantic import BaseModel, Field


class CreateWalletRequest(BaseModel):
    """Body for creating a new wallet."""

    trader_id: str = Field(..., min_length=36, max_length=36)


class MoneyRequest(BaseModel):
    """Monetary amount with currency."""

    amount: Decimal = Field(..., gt=0, max_digits=18, decimal_places=2)
    currency: str = Field(..., min_length=3, max_length=3)


class AddHoldingRequest(BaseModel):
    """Body for adding shares to a holding."""

    instrument_id: str = Field(..., min_length=36, max_length=36)
    quantity: int = Field(..., gt=0)
    average_cost: Decimal = Field(..., ge=0, max_digits=18, decimal_places=2)
    average_cost_currency: str = Field(..., min_length=3, max_length=3)


class QuantityRequest(BaseModel):
    """Body for operations that only need a share quantity."""

    quantity: int = Field(..., gt=0)


class HoldingQuantityRequest(BaseModel):
    """Body for holding operations identified by instrument and quantity."""

    instrument_id: str = Field(..., min_length=36, max_length=36)
    quantity: int = Field(..., gt=0)
