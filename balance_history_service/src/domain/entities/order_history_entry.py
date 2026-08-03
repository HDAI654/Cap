from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class OrderHistoryEntry:
    """Append-only projection of an order lifecycle event."""

    entry_id: str
    order_id: str
    trader_id: str
    instrument_id: str
    event_type: str
    side: str | None
    order_type: str | None
    quantity: int | None
    filled_quantity: int | None
    remaining_quantity: int | None
    price: Decimal | None
    price_currency: str | None
    status: str | None
    occurred_at: datetime
