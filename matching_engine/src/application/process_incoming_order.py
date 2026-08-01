import logging
from dataclasses import dataclass
from decimal import Decimal

from src.domain.entities.order_book import MatchResult, OrderBook
from src.domain.events.matching_events import (
    OrderFilled,
    OrderPlaced,
    TradeExecuted,
)
from src.domain.ports.event_publisher import EventPublisher
from src.domain.ports.market_data_cache import MarketDataCache
from src.domain.ports.order_book_registry import OrderBookRegistry
from src.domain.value_objects.currency import Currency
from src.domain.value_objects.instrument_id import InstrumentId
from src.domain.value_objects.money import Money
from src.domain.value_objects.order_id import OrderId
from src.domain.value_objects.order_side import OrderSide
from src.domain.value_objects.order_type import OrderType
from src.domain.value_objects.quantity import Quantity
from src.domain.value_objects.time_in_force import TimeInForce
from src.domain.value_objects.trader_id import TraderId
from src.exceptions import InvalidIncomingOrderError

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ProcessIncomingOrderCommand:
    """Command derived from OrderOpened / OrderSubmitted events."""

    order_id: str
    trader_id: str
    instrument_id: str
    side: str
    order_type: str
    time_in_force: str
    quantity: int
    limit_price: Decimal | None = None
    limit_price_currency: str | None = None


class ProcessIncomingOrderHandler:
    """Match an incoming order against the in-memory book and emit events."""

    def __init__(
        self,
        registry: OrderBookRegistry,
        event_publisher: EventPublisher,
        market_data_cache: MarketDataCache,
    ) -> None:
        self._registry = registry
        self._event_publisher = event_publisher
        self._cache = market_data_cache

    async def handle(self, command: ProcessIncomingOrderCommand) -> MatchResult:
        logger.info(
            "Processing incoming order: order_id=%s instrument=%s side=%s type=%s qty=%s",
            command.order_id,
            command.instrument_id,
            command.side,
            command.order_type,
            command.quantity,
        )

        order_id = OrderId(command.order_id)
        trader_id = TraderId(command.trader_id)
        instrument_id = InstrumentId(command.instrument_id)
        side = self._parse_side(command.side)
        order_type = self._parse_order_type(command.order_type)
        time_in_force = self._parse_tif(command.time_in_force)
        quantity = Quantity(command.quantity)
        limit_price = self._parse_limit_price(
            command.limit_price,
            command.limit_price_currency,
            order_type,
        )

        book = self._registry.get_or_create(instrument_id)
        result = book.submit(
            order_id=order_id,
            trader_id=trader_id,
            side=side,
            order_type=order_type,
            time_in_force=time_in_force,
            quantity=quantity,
            limit_price=limit_price,
        )

        await self._publish_result(command, result, book)
        await self._update_cache(book)

        logger.info(
            "Order processed: order_id=%s trades=%s filled=%s remaining=%s rested=%s",
            command.order_id,
            len(result.trades),
            result.taker_filled_quantity,
            result.taker_remaining_quantity,
            result.resting_order is not None,
        )
        return result

    async def _publish_result(
        self,
        command: ProcessIncomingOrderCommand,
        result: MatchResult,
        book: OrderBook,
    ) -> None:
        for trade in result.trades:
            await self._event_publisher.publish(
                TradeExecuted(
                    trade_id=trade.id.value,
                    maker_order_id=trade.maker_order_id.value,
                    taker_order_id=trade.taker_order_id.value,
                    buyer_id=trade.buyer_id.value,
                    seller_id=trade.seller_id.value,
                    instrument_id=trade.instrument_id.value,
                    quantity=trade.quantity.value,
                    execution_price=trade.execution_price.amount,
                    execution_price_currency=trade.execution_price.currency.value,
                    sequence_number=trade.sequence_number,
                )
            )

        if result.taker_filled_quantity > 0:
            await self._event_publisher.publish(
                OrderFilled(
                    order_id=command.order_id,
                    trader_id=command.trader_id,
                    instrument_id=command.instrument_id,
                    side=command.side,
                    fill_quantity=result.taker_filled_quantity,
                    remaining_quantity=result.taker_remaining_quantity,
                    is_fully_filled=result.taker_fully_filled,
                )
            )

            # Maker fills are implied by TradeExecuted; downstream can derive.

        if result.resting_order is not None:
            resting = result.resting_order
            await self._event_publisher.publish(
                OrderPlaced(
                    order_id=resting.order_id.value,
                    trader_id=resting.trader_id.value,
                    instrument_id=resting.instrument_id.value,
                    side=resting.side.value,
                    price=resting.price.amount,
                    price_currency=resting.price.currency.value,
                    quantity=resting.remaining_quantity.value,
                )
            )

    async def _update_cache(self, book: OrderBook) -> None:
        last = book.last_trade_price
        if last is not None:
            await self._cache.write_last_trade_price(
                book.instrument_id,
                last.amount,
                last.currency.value,
            )

        bids = [(p.amount, q) for p, q in book.depth_bids()]
        asks = [(p.amount, q) for p, q in book.depth_asks()]
        await self._cache.write_book_snapshot(
            book.instrument_id,
            bids,
            asks,
            last.amount if last is not None else None,
            last.currency.value if last is not None else None,
        )

    @staticmethod
    def _parse_side(value: str) -> OrderSide:
        try:
            return OrderSide(value)
        except ValueError as exc:
            raise InvalidIncomingOrderError(f"Invalid side: {value}") from exc

    @staticmethod
    def _parse_order_type(value: str) -> OrderType:
        try:
            return OrderType(value)
        except ValueError as exc:
            raise InvalidIncomingOrderError(f"Invalid order type: {value}") from exc

    @staticmethod
    def _parse_tif(value: str) -> TimeInForce:
        try:
            return TimeInForce(value)
        except ValueError as exc:
            raise InvalidIncomingOrderError(f"Invalid time in force: {value}") from exc

    @staticmethod
    def _parse_limit_price(
        amount: Decimal | None,
        currency_code: str | None,
        order_type: OrderType,
    ) -> Money | None:
        if order_type is OrderType.MARKET:
            return None
        if amount is None or currency_code is None:
            raise InvalidIncomingOrderError("LIMIT orders require a limit price.")
        try:
            currency = Currency(currency_code)
        except ValueError as exc:
            raise InvalidIncomingOrderError(
                f"Invalid currency: {currency_code}"
            ) from exc
        return Money(amount, currency)
