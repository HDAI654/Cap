import logging
from dataclasses import dataclass
from decimal import Decimal

from src.domain.factories.order_factory import OrderFactory
from src.domain.ports.unit_of_work import UnitOfWork
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
    """Application service that submits a new order."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def handle(self, command: SubmitOrderCommand) -> SubmitOrderResult:
        """Submit a new order.

        Raises:
            OrderAlreadyExistsError: If an order already exists for the
                trader and idempotency key.
            InvalidOrderParametersError: If command fields violate domain rules.
        """
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
            await self._uow.commit()
            order.clear_changes()

            logger.info("Order submitted successfully: order_id=%s", order.id.value)

            return SubmitOrderResult(order_id=order.id.value)

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
