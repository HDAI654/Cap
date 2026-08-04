from abc import ABC, abstractmethod

from src.domain.ports.order_repository import OrderRepository


class UnitOfWork(ABC):
    """Coordinates repositories and transaction boundaries."""

    orders: OrderRepository

    @abstractmethod
    async def __aenter__(self) -> "UnitOfWork":
        """Enter the transactional context."""
        raise NotImplementedError

    @abstractmethod
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: object,
    ) -> None:
        """Exit the transactional context."""
        raise NotImplementedError

    @abstractmethod
    async def commit(self) -> None:
        """Commit the current transaction."""
        raise NotImplementedError

    @abstractmethod
    async def rollback(self) -> None:
        """Rollback the current transaction."""
        raise NotImplementedError
