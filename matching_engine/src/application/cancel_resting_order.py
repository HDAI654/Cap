import logging
from dataclasses import dataclass

from src.domain.events.matching_events import OrderRemoved
from src.domain.ports.event_publisher import EventPublisher
from src.domain.ports.market_data_cache import MarketDataCache
from src.domain.ports.order_book_registry import OrderBookRegistry
from src.domain.value_objects.instrument_id import InstrumentId
from src.domain.value_objects.order_id import OrderId
from src.exceptions import OrderNotInBookError

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class CancelRestingOrderCommand:
    order_id: str
    instrument_id: str


class CancelRestingOrderHandler:
    """Remove a resting order from the book (reacts to OrderCancelled)."""

    def __init__(
        self,
        registry: OrderBookRegistry,
        event_publisher: EventPublisher,
        market_data_cache: MarketDataCache,
    ) -> None:
        self._registry = registry
        self._event_publisher = event_publisher
        self._cache = market_data_cache

    async def handle(self, command: CancelRestingOrderCommand) -> None:
        logger.info(
            "Cancelling resting order: order_id=%s instrument=%s",
            command.order_id,
            command.instrument_id,
        )

        order_id = OrderId(command.order_id)
        instrument_id = InstrumentId(command.instrument_id)
        book = self._registry.get(instrument_id)
        if book is None:
            raise OrderNotInBookError(
                f"No book for instrument '{command.instrument_id}'."
            )

        removed = book.cancel(order_id)

        await self._event_publisher.publish(
            OrderRemoved(
                order_id=removed.order_id.value,
                trader_id=removed.trader_id.value,
                instrument_id=removed.instrument_id.value,
                side=removed.side.value,
                remaining_quantity=removed.remaining_quantity.value,
            )
        )

        last = book.last_trade_price
        await self._cache.write_book_snapshot(
            book.instrument_id,
            [(p.amount, q) for p, q in book.depth_bids()],
            [(p.amount, q) for p, q in book.depth_asks()],
            last.amount if last is not None else None,
            last.currency.value if last is not None else None,
        )

        logger.info("Resting order cancelled: order_id=%s", command.order_id)
