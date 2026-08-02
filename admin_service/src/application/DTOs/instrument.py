from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class InstrumentDTO:
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
