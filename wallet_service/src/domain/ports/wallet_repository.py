from abc import ABC, abstractmethod
from wallet_service.src.domain.entities.wallet import Wallet
from wallet_service.src.domain.value_objects.trader_id import TraderId
from wallet_service.src.domain.value_objects.wallet_id import WalletId


class WalletRepository(ABC):
    """Repository interface for Wallet aggregates."""

    @abstractmethod
    async def add(self, wallet: Wallet) -> None:
        """Persist a new wallet."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(
        self,
        wallet_id: WalletId,
    ) -> Wallet | None:
        """Retrieve a wallet by its identifier."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_trader_id(
        self,
        trader_id: TraderId,
    ) -> Wallet | None:
        """Retrieve a wallet by trader identifier."""
        raise NotImplementedError

    @abstractmethod
    async def update(self, wallet: Wallet) -> None:
        """Persist changes to a wallet."""
        raise NotImplementedError

    @abstractmethod
    async def delete(
        self,
        wallet_id: WalletId,
    ) -> None:
        """Delete a wallet."""
        raise NotImplementedError

    @abstractmethod
    async def exists_by_trader_id(
        self,
        trader_id: TraderId,
    ) -> bool:
        """Return whether a wallet exists for the trader."""
        raise NotImplementedError
