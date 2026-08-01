import logging
from dataclasses import dataclass

from src.application.DTOs import OrderDTO
from src.domain.entities.order import Order
from src.domain.ports.unit_of_work import UnitOfWork
from src.domain.value_objects.order_id import OrderId

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class GetOrderQuery:
    """Input for the get-order use case."""

    order_id: str


class GetOrderHandler:
    """Application service that retrieves an order by identifier."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def handle(self, query: GetOrderQuery) -> OrderDTO:
        """Retrieve an order."""
        logger.info("Retrieving order: order_id=%s", query.order_id)

        order_id = OrderId(query.order_id)

        async with self._uow:
            order = await self._uow.orders.get_by_id(order_id)

            logger.info("Order retrieved successfully: order_id=%s", query.order_id)

            return _to_dto(order)


def _to_dto(order: Order) -> OrderDTO:
    limit_price = order.limit_price
    return OrderDTO(
        order_id=order.id.value,
        trader_id=order.trader_id.value,
        instrument_id=order.instrument_id.value,
        side=order.side.value,
        order_type=order.order_type.value,
        time_in_force=order.time_in_force.value,
        quantity=order.quantity.value,
        filled_quantity=order.filled_quantity.value,
        remaining_quantity=order.remaining_quantity.value,
        limit_price=limit_price.amount if limit_price is not None else None,
        limit_price_currency=(
            limit_price.currency.value if limit_price is not None else None
        ),
        status=order.status.value,
        idempotency_key=order.idempotency_key.value,
        created_at=order.created_at,
        updated_at=order.updated_at,
    )
