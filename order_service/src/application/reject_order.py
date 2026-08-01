import logging
from dataclasses import dataclass

from src.domain.ports.unit_of_work import UnitOfWork
from src.domain.value_objects.order_id import OrderId

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class RejectOrderCommand:
    """Input for the reject-order use case."""

    order_id: str


class RejectOrderHandler:
    """Application service that rejects a NEW order."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def handle(self, command: RejectOrderCommand) -> None:
        """Reject the given order."""
        logger.info("Rejecting order: order_id=%s", command.order_id)

        order_id = OrderId(command.order_id)

        async with self._uow:
            order = await self._uow.orders.get_by_id(order_id)

            order.reject()

            if order.is_changed():
                await self._uow.orders.update(order)
                await self._uow.commit()
                order.clear_changes()

        logger.info("Order rejected successfully: order_id=%s", command.order_id)
