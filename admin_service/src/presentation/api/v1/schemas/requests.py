from decimal import Decimal

from pydantic import BaseModel, Field


class CreateInstrumentRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=32)
    name: str = Field(..., min_length=1, max_length=255)
    tick_size: Decimal = Field(..., gt=0, max_digits=18, decimal_places=2)
    lot_size: int = Field(..., gt=0)
    minimum_order_quantity: int = Field(..., gt=0)
    maximum_order_quantity: int = Field(..., gt=0)
    currency: str = Field(..., min_length=3, max_length=3)
    total_shares: int = Field(default=0, ge=0)


class AllocateSharesRequest(BaseModel):
    quantity: int = Field(..., gt=0)
