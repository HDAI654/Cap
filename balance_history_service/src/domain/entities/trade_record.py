from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class TradeRecord:
    """Persisted projection of a TradeExecuted event."""

    trade_id: str
    maker_order_id: str
    taker_order_id: str
    buyer_id: str
    seller_id: str
    instrument_id: str
    quantity: int
    execution_price: Decimal
    execution_price_currency: str
    sequence_number: int
    executed_at: datetime
