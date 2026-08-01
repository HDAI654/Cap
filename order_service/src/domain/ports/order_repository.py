from abc import ABC, abstractmethod
from src.domain.entities.order import Order
from src.domain.value_objects.idempotency_key import IdempotencyKey
from src.domain.value_objects.order_id import OrderId
from src.domain.value_objects.trader_id import TraderId


class OrderRepository(ABC):
    """Repository interface for Order aggregates."""

    @abstractmethod
    async def add(self, order: Order) -> None:
        """Persist a new order."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, order_id: OrderId) -> Order:
        """Retrieve an order by its identifier.

        Raises:
            OrderNotFoundError: If no order exists for the given identifier.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_by_idempotency_key(
        self,
        trader_id: TraderId,
        idempotency_key: IdempotencyKey,
    ) -> Order | None:
        """Retrieve an order by trader and idempotency key, or None if absent."""
        raise NotImplementedError

    @abstractmethod
    async def update(self, order: Order) -> None:
        """Persist changes to an order.

        Raises:
            OrderNotFoundError: If no order exists for the given identifier.
        """
        raise NotImplementedError

    @abstractmethod
    async def list_by_trader(
        self,
        trader_id: TraderId,
    ) -> list[Order]:
        """Return all orders placed by the trader."""
        raise NotImplementedError
