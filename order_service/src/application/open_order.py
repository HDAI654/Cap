import logging
from dataclasses import dataclass

from src.domain.events.order_events import OrderOpened
from src.domain.ports.event_publisher import EventPublisher
from src.domain.ports.unit_of_work import UnitOfWork
from src.domain.value_objects.order_id import OrderId

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class OpenOrderCommand:
    """Input for the open-order use case."""

    order_id: str


class OpenOrderHandler:
    """Application service that opens a NEW order onto the book."""

    def __init__(
        self,
        uow: UnitOfWork,
        event_publisher: EventPublisher,
    ) -> None:
        self._uow = uow
        self._event_publisher = event_publisher

    async def handle(self, command: OpenOrderCommand) -> None:
        """Open the given order (NEW → OPEN) and publish OrderOpened."""
        logger.info("Opening order: order_id=%s", command.order_id)

        order_id = OrderId(command.order_id)
        published = False

        async with self._uow:
            order = await self._uow.orders.get_by_id(order_id)

            order.open()

            if order.is_changed():
                await self._uow.orders.update(order)
                await self._uow.commit()
                order.clear_changes()
                published = True

        if published:
            limit = order.limit_price
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

        logger.info("Order opened successfully: order_id=%s", command.order_id)
