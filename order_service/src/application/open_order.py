import logging
from dataclasses import dataclass

from src.domain.ports.unit_of_work import UnitOfWork
from src.domain.value_objects.order_id import OrderId

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class OpenOrderCommand:
    """Input for the open-order use case."""

    order_id: str


class OpenOrderHandler:
    """Application service that opens a NEW order onto the book."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def handle(self, command: OpenOrderCommand) -> None:
        """Open the given order (NEW → OPEN)."""
        logger.info("Opening order: order_id=%s", command.order_id)

        order_id = OrderId(command.order_id)

        async with self._uow:
            order = await self._uow.orders.get_by_id(order_id)

            order.open()

            if order.is_changed():
                await self._uow.orders.update(order)
                await self._uow.commit()
                order.clear_changes()

        logger.info("Order opened successfully: order_id=%s", command.order_id)
