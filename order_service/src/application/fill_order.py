import logging
from dataclasses import dataclass

from src.domain.events.order_events import OrderFilled
from src.domain.ports.event_publisher import EventPublisher
from src.domain.ports.unit_of_work import UnitOfWork
from src.domain.value_objects.order_id import OrderId
from src.domain.value_objects.quantity import Quantity

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class FillOrderCommand:
    """Input for the fill-order use case."""

    order_id: str
    fill_quantity: int


class FillOrderHandler:
    """Application service that applies a fill to an order."""

    def __init__(
        self,
        uow: UnitOfWork,
        event_publisher: EventPublisher,
    ) -> None:
        self._uow = uow
        self._event_publisher = event_publisher

    async def handle(self, command: FillOrderCommand) -> None:
        """Apply a fill and publish OrderFilled."""
        logger.info(
            "Filling order: order_id=%s, fill_quantity=%s",
            command.order_id,
            command.fill_quantity,
        )

        order_id = OrderId(command.order_id)
        fill_quantity = Quantity(command.fill_quantity)

        async with self._uow:
            order = await self._uow.orders.get_by_id(order_id)

            order.fill(fill_quantity)
            await self._uow.orders.update(order)
            await self._uow.commit()
            order.clear_changes()

        await self._event_publisher.publish(
            OrderFilled(
                order_id=order.id.value,
                trader_id=order.trader_id.value,
                instrument_id=order.instrument_id.value,
                side=order.side.value,
                fill_quantity=fill_quantity.value,
                filled_quantity=order.filled_quantity.value,
                remaining_quantity=order.remaining_quantity.value,
                status=order.status.value,
            )
        )

        logger.info(
            "Order filled successfully: order_id=%s, fill_quantity=%s",
            command.order_id,
            command.fill_quantity,
        )
