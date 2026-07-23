from abc import ABC, abstractmethod
from wallet_service.src.domain.ports.wallet_repository import (
    WalletRepository,
)


class UnitOfWork(ABC):
    """Coordinates repositories and transaction boundaries."""

    wallets: WalletRepository

    @abstractmethod
    async def __aenter__(self) -> "UnitOfWork":
        """Enter the transactional context."""
        raise NotImplementedError

    @abstractmethod
    async def __aexit__(
        self,
        exc_type,
        exc,
        tb,
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
