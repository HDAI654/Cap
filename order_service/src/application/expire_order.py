import logging
from dataclasses import dataclass

from src.domain.events.order_events import OrderExpired
from src.domain.ports.event_publisher import EventPublisher
from src.domain.ports.unit_of_work import UnitOfWork
from src.domain.value_objects.order_id import OrderId

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ExpireOrderCommand:
    """Input for the expire-order use case."""

    order_id: str


class ExpireOrderHandler:
    """Application service that expires an order still on the book."""

    def __init__(
        self,
        uow: UnitOfWork,
        event_publisher: EventPublisher,
    ) -> None:
        self._uow = uow
        self._event_publisher = event_publisher

    async def handle(self, command: ExpireOrderCommand) -> None:
        """Expire the given order and publish OrderExpired."""
        logger.info("Expiring order: order_id=%s", command.order_id)

        order_id = OrderId(command.order_id)
        published = False

        async with self._uow:
            order = await self._uow.orders.get_by_id(order_id)

            order.expire()

            if order.is_changed():
                await self._uow.orders.update(order)
                await self._uow.commit()
                order.clear_changes()
                published = True

        if published:
            await self._event_publisher.publish(
                OrderExpired(
                    order_id=order.id.value,
                    trader_id=order.trader_id.value,
                    instrument_id=order.instrument_id.value,
                    side=order.side.value,
                    filled_quantity=order.filled_quantity.value,
                    remaining_quantity=order.remaining_quantity.value,
                )
            )

        logger.info("Order expired successfully: order_id=%s", command.order_id)
