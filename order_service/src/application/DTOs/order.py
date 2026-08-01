from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class OrderDTO:
    """Full order projection returned to the presentation layer."""

    order_id: str
    trader_id: str
    instrument_id: str
    side: str
    order_type: str
    time_in_force: str
    quantity: int
    filled_quantity: int
    remaining_quantity: int
    limit_price: Decimal | None
    limit_price_currency: str | None
    status: str
    idempotency_key: str
    created_at: datetime
    updated_at: datetime
