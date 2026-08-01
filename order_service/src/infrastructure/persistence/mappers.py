from src.domain.entities.order import Order
from src.domain.value_objects.currency import Currency
from src.domain.value_objects.idempotency_key import IdempotencyKey
from src.domain.value_objects.instrument_id import InstrumentId
from src.domain.value_objects.money import Money
from src.domain.value_objects.order_id import OrderId
from src.domain.value_objects.order_side import OrderSide
from src.domain.value_objects.order_status import OrderStatus
from src.domain.value_objects.order_type import OrderType
from src.domain.value_objects.quantity import Quantity
from src.domain.value_objects.time_in_force import TimeInForce
from src.domain.value_objects.trader_id import TraderId
from src.infrastructure.persistence.models import OrderModel


def order_to_model(order: Order) -> OrderModel:
    """Convert a domain Order aggregate into a new ORM model."""
    limit_price = order.limit_price
    return OrderModel(
        id=order.id.value,
        trader_id=order.trader_id.value,
        instrument_id=order.instrument_id.value,
        side=order.side.value,
        order_type=order.order_type.value,
        time_in_force=order.time_in_force.value,
        quantity=order.quantity.value,
        filled_quantity=order.filled_quantity.value,
        limit_price=limit_price.amount if limit_price is not None else None,
        limit_price_currency=(
            limit_price.currency.value if limit_price is not None else None
        ),
        status=order.status.value,
        idempotency_key=order.idempotency_key.value,
        created_at=order.created_at,
        updated_at=order.updated_at,
    )


def model_to_order(model: OrderModel) -> Order:
    """Reconstitute a domain Order aggregate from an ORM model."""
    limit_price: Money | None = None
    if model.limit_price is not None and model.limit_price_currency is not None:
        limit_price = Money(
            model.limit_price,
            Currency(model.limit_price_currency),
        )

    return Order(
        id=OrderId(model.id),
        trader_id=TraderId(model.trader_id),
        instrument_id=InstrumentId(model.instrument_id),
        side=OrderSide(model.side),
        order_type=OrderType(model.order_type),
        time_in_force=TimeInForce(model.time_in_force),
        quantity=Quantity(model.quantity),
        filled_quantity=Quantity(model.filled_quantity),
        limit_price=limit_price,
        status=OrderStatus(model.status),
        idempotency_key=IdempotencyKey(model.idempotency_key),
        created_at=model.created_at,
        updated_at=model.updated_at,
    )
