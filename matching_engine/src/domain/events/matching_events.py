from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class DomainEvent:
    """Base integration event published to the event bus."""

    event_type: str
    occurred_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc),
    )


@dataclass(frozen=True, slots=True)
class TradeExecuted(DomainEvent):
    """A trade was matched between maker and taker."""

    trade_id: str = ""
    maker_order_id: str = ""
    taker_order_id: str = ""
    buyer_id: str = ""
    seller_id: str = ""
    instrument_id: str = ""
    quantity: int = 0
    execution_price: Decimal | None = None
    execution_price_currency: str | None = None
    sequence_number: int = 0
    event_type: str = "TradeExecuted"


@dataclass(frozen=True, slots=True)
class OrderFilled(DomainEvent):
    """An order received a fill (partial or full) on the book."""

    order_id: str = ""
    trader_id: str = ""
    instrument_id: str = ""
    side: str = ""
    fill_quantity: int = 0
    remaining_quantity: int = 0
    is_fully_filled: bool = False
    event_type: str = "OrderFilled"


@dataclass(frozen=True, slots=True)
class OrderPlaced(DomainEvent):
    """A residual limit order was placed (rested) on the book."""

    order_id: str = ""
    trader_id: str = ""
    instrument_id: str = ""
    side: str = ""
    price: Decimal | None = None
    price_currency: str | None = None
    quantity: int = 0
    event_type: str = "OrderPlaced"


@dataclass(frozen=True, slots=True)
class OrderRemoved(DomainEvent):
    """A resting order was removed from the book (cancel)."""

    order_id: str = ""
    trader_id: str = ""
    instrument_id: str = ""
    side: str = ""
    remaining_quantity: int = 0
    event_type: str = "OrderRemoved"
