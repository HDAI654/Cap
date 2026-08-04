import logging
from dataclasses import dataclass
from decimal import Decimal

from src.domain.events.order_events import OrderOpened, OrderSubmitted
from src.domain.factories.order_factory import OrderFactory
from src.domain.ports.event_publisher import EventPublisher
from src.domain.ports.instrument_gateway import InstrumentGateway
from src.domain.ports.unit_of_work import UnitOfWork
from src.domain.ports.wallet_gateway import WalletGateway
from src.domain.value_objects.currency import Currency
from src.domain.value_objects.idempotency_key import IdempotencyKey
from src.domain.value_objects.instrument_id import InstrumentId
from src.domain.value_objects.money import Money
from src.domain.value_objects.order_side import OrderSide
from src.domain.value_objects.order_type import OrderType
from src.domain.value_objects.quantity import Quantity
from src.domain.value_objects.time_in_force import TimeInForce
from src.domain.value_objects.trader_id import TraderId
from src.exceptions import InvalidOrderParametersError, OrderAlreadyExistsError
from src.infrastructure.http_clients.noop_instrument_gateway import (
    NoOpInstrumentGateway,
)
from src.infrastructure.http_clients.noop_wallet_gateway import NoOpWalletGateway

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class SubmitOrderCommand:
    """Input for the submit-order use case."""

    trader_id: str
    instrument_id: str
    side: str
    order_type: str
    time_in_force: str
    quantity: int
    idempotency_key: str
    limit_price: Decimal | None = None
    limit_price_currency: str | None = None


@dataclass(frozen=True, slots=True)
class SubmitOrderResult:
    """Output of the submit-order use case."""

    order_id: str


class SubmitOrderHandler:
    """Submit a new order, reserve funds, open it, and publish lifecycle events.

    Flow:
        1. Validate instrument is tradable (Admin).
        2. Reserve cash (BUY) or holdings (SELL) via Wallet.
        3. Persist NEW → OPEN in one unit of work.
        4. Publish OrderSubmitted and OrderOpened (ME matches on Opened).
    """

    def __init__(
        self,
        uow: UnitOfWork,
        event_publisher: EventPublisher,
        wallet_gateway: WalletGateway | None = None,
        instrument_gateway: InstrumentGateway | None = None,
    ) -> None:
        self._uow = uow
        self._event_publisher = event_publisher
        self._wallet = wallet_gateway or NoOpWalletGateway()
        self._instruments = instrument_gateway or NoOpInstrumentGateway()

    async def handle(self, command: SubmitOrderCommand) -> SubmitOrderResult:
        logger.info(
            "Submitting order: trader_id=%s, instrument_id=%s, side=%s, "
            "type=%s, quantity=%s, idempotency_key=%s",
            command.trader_id,
            command.instrument_id,
            command.side,
            command.order_type,
            command.quantity,
            command.idempotency_key,
        )

        trader_id = TraderId(command.trader_id)
        instrument_id = InstrumentId(command.instrument_id)
        idempotency_key = IdempotencyKey(command.idempotency_key)
        quantity = Quantity(command.quantity)

        side = self._parse_side(command.side)
        order_type = self._parse_order_type(command.order_type)
        time_in_force = self._parse_time_in_force(command.time_in_force)
        limit_price = self._parse_limit_price(
            command.limit_price,
            command.limit_price_currency,
            order_type,
        )

        await self._instruments.ensure_tradable(command.instrument_id)

        await self._reserve(command, side, order_type, limit_price)

        async with self._uow:
            existing = await self._uow.orders.get_by_idempotency_key(
                trader_id,
                idempotency_key,
            )
            if existing is not None:
                raise OrderAlreadyExistsError(
                    f"Order already exists for trader '{command.trader_id}' "
                    f"with idempotency key '{command.idempotency_key}'."
                )

            order = OrderFactory.create(
                trader_id=trader_id,
                instrument_id=instrument_id,
                side=side,
                order_type=order_type,
                time_in_force=time_in_force,
                quantity=quantity,
                idempotency_key=idempotency_key,
                limit_price=limit_price,
            )
            await self._uow.orders.add(order)

            # Accept onto the book immediately so ME can match (NEW → OPEN).
            order.open()
            await self._uow.orders.update(order)
            await self._uow.commit()
            order.clear_changes()

        limit = order.limit_price
        await self._event_publisher.publish(
            OrderSubmitted(
                order_id=order.id.value,
                trader_id=order.trader_id.value,
                instrument_id=order.instrument_id.value,
                side=order.side.value,
                order_type=order.order_type.value,
                time_in_force=order.time_in_force.value,
                quantity=order.quantity.value,
                limit_price=limit.amount if limit is not None else None,
                limit_price_currency=(
                    limit.currency.value if limit is not None else None
                ),
                idempotency_key=order.idempotency_key.value,
            )
        )
        await self._event_publisher.publish(
            OrderOpened(
                order_id=order.id.value,
                trader_id=order.trader_id.value,
                instrument_id=order.instrument_id.value,
                side=order.side.value,
                order_type=order.order_type.value,
                time_in_force=order.time_in_force.value,
                quantity=order.quantity.value,
                remaining_quantity=order.remaining_quantity.value,
                limit_price=limit.amount if limit is not None else None,
                limit_price_currency=(
                    limit.currency.value if limit is not None else None
                ),
            )
        )

        logger.info(
            "Order submitted and opened: order_id=%s",
            order.id.value,
        )
        return SubmitOrderResult(order_id=order.id.value)

    async def _reserve(
        self,
        command: SubmitOrderCommand,
        side: OrderSide,
        order_type: OrderType,
        limit_price: Money | None,
    ) -> None:
        if side is OrderSide.BUY:
            if order_type is OrderType.LIMIT and limit_price is not None:
                notional = limit_price.amount * Decimal(command.quantity)
                await self._wallet.reserve_for_buy(
                    command.trader_id,
                    notional,
                    limit_price.currency.value,
                )
            # MARKET buys: reservation requires LTP; deferred when no price.
            return

        await self._wallet.reserve_for_sell(
            command.trader_id,
            command.instrument_id,
            command.quantity,
        )

    @staticmethod
    def _parse_side(value: str) -> OrderSide:
        try:
            return OrderSide(value)
        except ValueError as exc:
            raise InvalidOrderParametersError(f"Invalid order side: {value}") from exc

    @staticmethod
    def _parse_order_type(value: str) -> OrderType:
        try:
            return OrderType(value)
        except ValueError as exc:
            raise InvalidOrderParametersError(f"Invalid order type: {value}") from exc

    @staticmethod
    def _parse_time_in_force(value: str) -> TimeInForce:
        try:
            return TimeInForce(value)
        except ValueError as exc:
            raise InvalidOrderParametersError(
                f"Invalid time in force: {value}"
            ) from exc

    @staticmethod
    def _parse_limit_price(
        amount: Decimal | None,
        currency_code: str | None,
        order_type: OrderType,
    ) -> Money | None:
        if order_type is OrderType.MARKET:
            if amount is not None or currency_code is not None:
                raise InvalidOrderParametersError(
                    "MARKET orders must not specify a limit price."
                )
            return None

        if amount is None or currency_code is None:
            return None

        try:
            currency = Currency(currency_code)
        except ValueError as exc:
            raise InvalidOrderParametersError(
                f"Invalid limit price currency: {currency_code}"
            ) from exc

        return Money(amount, currency)
