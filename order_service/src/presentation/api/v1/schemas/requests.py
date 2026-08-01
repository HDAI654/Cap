from decimal import Decimal

from pydantic import BaseModel, Field


class SubmitOrderRequest(BaseModel):
    """Body for submitting a new order."""

    trader_id: str = Field(..., min_length=36, max_length=36)
    instrument_id: str = Field(..., min_length=36, max_length=36)
    side: str = Field(..., min_length=3, max_length=8)
    order_type: str = Field(..., min_length=5, max_length=16)
    time_in_force: str = Field(..., min_length=3, max_length=8)
    quantity: int = Field(..., gt=0)
    idempotency_key: str = Field(..., min_length=1, max_length=128)
    limit_price: Decimal | None = Field(
        default=None,
        gt=0,
        max_digits=18,
        decimal_places=2,
    )
    limit_price_currency: str | None = Field(
        default=None,
        min_length=3,
        max_length=3,
    )


class FillOrderRequest(BaseModel):
    """Body for applying a fill to an order."""

    fill_quantity: int = Field(..., gt=0)
