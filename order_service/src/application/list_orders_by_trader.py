import logging
from dataclasses import dataclass

from src.application.DTOs import OrderDTO
from src.application.get_order import _to_dto
from src.domain.ports.unit_of_work import UnitOfWork
from src.domain.value_objects.trader_id import TraderId

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ListOrdersByTraderQuery:
    """Input for the list-orders-by-trader use case."""

    trader_id: str


class ListOrdersByTraderHandler:
    """Application service that lists all orders for a trader."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def handle(self, query: ListOrdersByTraderQuery) -> list[OrderDTO]:
        """Return all orders placed by the trader."""
        logger.info("Listing orders for trader: trader_id=%s", query.trader_id)

        trader_id = TraderId(query.trader_id)

        async with self._uow:
            orders = await self._uow.orders.list_by_trader(trader_id)

            logger.info(
                "Orders listed successfully: trader_id=%s, count=%s",
                query.trader_id,
                len(orders),
            )

            return [_to_dto(order) for order in orders]
