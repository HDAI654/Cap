from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class PriceLevel:
    """Quantity available at a single price."""

    price: Decimal
    quantity: int


@dataclass(frozen=True, slots=True)
class OrderBookSnapshot:
    """Read model of the current book for one instrument (from cache)."""

    instrument_id: str
    bids: tuple[PriceLevel, ...]
    asks: tuple[PriceLevel, ...]
    last_trade_price: Decimal | None
    last_trade_currency: str | None


@dataclass(frozen=True, slots=True)
class LastTradePrice:
    """Last traded price for an instrument."""

    instrument_id: str
    price: Decimal
    currency: str
