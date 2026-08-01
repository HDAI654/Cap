import logging
from dataclasses import dataclass

from src.domain.ports.unit_of_work import UnitOfWork
from src.domain.value_objects.order_id import OrderId

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class CancelOrderCommand:
    """Input for the cancel-order use case."""

    order_id: str


class CancelOrderHandler:
    """Application service that cancels an active order."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def handle(self, command: CancelOrderCommand) -> None:
        """Cancel the given order."""
        logger.info("Cancelling order: order_id=%s", command.order_id)

        order_id = OrderId(command.order_id)

        async with self._uow:
            order = await self._uow.orders.get_by_id(order_id)

            order.cancel()

            if order.is_changed():
                await self._uow.orders.update(order)
                await self._uow.commit()
                order.clear_changes()

        logger.info("Order cancelled successfully: order_id=%s", command.order_id)
