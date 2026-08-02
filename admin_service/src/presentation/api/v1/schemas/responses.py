from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class InstrumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    instrument_id: str
    symbol: str
    name: str
    tick_size: Decimal
    tick_size_currency: str
    lot_size: int
    minimum_order_quantity: int
    maximum_order_quantity: int
    currency: str
    total_shares: int
    status: str
    created_at: datetime
    updated_at: datetime


class CreateInstrumentResponse(BaseModel):
    instrument_id: str
