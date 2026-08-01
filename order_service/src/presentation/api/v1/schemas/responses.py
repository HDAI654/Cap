from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class OrderResponse(BaseModel):
    """Full order projection returned by GET endpoints."""

    model_config = ConfigDict(from_attributes=True)

    order_id: str
    trader_id: str
    instrument_id: str
    side: str
    order_type: str
    time_in_force: str
    quantity: int
    filled_quantity: int
    remaining_quantity: int
    limit_price: Decimal | None = None
    limit_price_currency: str | None = None
    status: str
    idempotency_key: str
    created_at: datetime
    updated_at: datetime


class SubmitOrderResponse(BaseModel):
    """Response after submitting an order."""

    order_id: str


class ErrorResponse(BaseModel):
    """Standard error body."""

    detail: str
