from src.domain.entities.order import Order
from src.domain.value_objects.idempotency_key import IdempotencyKey
from src.domain.value_objects.instrument_id import InstrumentId
from src.domain.value_objects.money import Money
from src.domain.value_objects.order_side import OrderSide
from src.domain.value_objects.order_type import OrderType
from src.domain.value_objects.quantity import Quantity
from src.domain.value_objects.time_in_force import TimeInForce
from src.domain.value_objects.trader_id import TraderId


class OrderFactory:
    """Factory for creating Order aggregates."""

    @staticmethod
    def create(
        trader_id: TraderId,
        instrument_id: InstrumentId,
        side: OrderSide,
        order_type: OrderType,
        time_in_force: TimeInForce,
        quantity: Quantity,
        idempotency_key: IdempotencyKey,
        limit_price: Money | None = None,
    ) -> Order:
        """Create a new order aggregate in NEW status."""
        return Order.create(
            trader_id=trader_id,
            instrument_id=instrument_id,
            side=side,
            order_type=order_type,
            time_in_force=time_in_force,
            quantity=quantity,
            idempotency_key=idempotency_key,
            limit_price=limit_price,
        )
