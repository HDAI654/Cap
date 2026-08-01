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
class OrderSubmitted(DomainEvent):
    """Emitted after a new order has been persisted."""

    order_id: str = ""
    trader_id: str = ""
    instrument_id: str = ""
    side: str = ""
    order_type: str = ""
    time_in_force: str = ""
    quantity: int = 0
    limit_price: Decimal | None = None
    limit_price_currency: str | None = None
    idempotency_key: str = ""
    event_type: str = "OrderSubmitted"


@dataclass(frozen=True, slots=True)
class OrderOpened(DomainEvent):
    """Emitted after a NEW order is accepted onto the book (NEW → OPEN)."""

    order_id: str = ""
    trader_id: str = ""
    instrument_id: str = ""
    side: str = ""
    order_type: str = ""
    quantity: int = 0
    remaining_quantity: int = 0
    event_type: str = "OrderOpened"


@dataclass(frozen=True, slots=True)
class OrderFilled(DomainEvent):
    """Emitted after a fill is applied to an order.

    May represent a partial or full fill; ``status`` is the resulting status.
    """

    order_id: str = ""
    trader_id: str = ""
    instrument_id: str = ""
    side: str = ""
    fill_quantity: int = 0
    filled_quantity: int = 0
    remaining_quantity: int = 0
    status: str = ""
    event_type: str = "OrderFilled"


@dataclass(frozen=True, slots=True)
class OrderCancelled(DomainEvent):
    """Emitted after an order has been cancelled."""

    order_id: str = ""
    trader_id: str = ""
    instrument_id: str = ""
    side: str = ""
    filled_quantity: int = 0
    remaining_quantity: int = 0
    event_type: str = "OrderCancelled"


@dataclass(frozen=True, slots=True)
class OrderRejected(DomainEvent):
    """Emitted after a NEW order is rejected."""

    order_id: str = ""
    trader_id: str = ""
    instrument_id: str = ""
    side: str = ""
    event_type: str = "OrderRejected"


@dataclass(frozen=True, slots=True)
class OrderExpired(DomainEvent):
    """Emitted after an order still on the book expires."""

    order_id: str = ""
    trader_id: str = ""
    instrument_id: str = ""
    side: str = ""
    filled_quantity: int = 0
    remaining_quantity: int = 0
    event_type: str = "OrderExpired"
