import logging
from dataclasses import dataclass

from src.domain.events.order_events import OrderRejected
from src.domain.ports.event_publisher import EventPublisher
from src.domain.ports.unit_of_work import UnitOfWork
from src.domain.value_objects.order_id import OrderId

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class RejectOrderCommand:
    """Input for the reject-order use case."""

    order_id: str


class RejectOrderHandler:
    """Application service that rejects a NEW order."""

    def __init__(
        self,
        uow: UnitOfWork,
        event_publisher: EventPublisher,
    ) -> None:
        self._uow = uow
        self._event_publisher = event_publisher

    async def handle(self, command: RejectOrderCommand) -> None:
        """Reject the given order and publish OrderRejected."""
        logger.info("Rejecting order: order_id=%s", command.order_id)

        order_id = OrderId(command.order_id)
        published = False

        async with self._uow:
            order = await self._uow.orders.get_by_id(order_id)

            order.reject()

            if order.is_changed():
                await self._uow.orders.update(order)
                await self._uow.commit()
                order.clear_changes()
                published = True

        if published:
            await self._event_publisher.publish(
                OrderRejected(
                    order_id=order.id.value,
                    trader_id=order.trader_id.value,
                    instrument_id=order.instrument_id.value,
                    side=order.side.value,
                )
            )

        logger.info("Order rejected successfully: order_id=%s", command.order_id)
