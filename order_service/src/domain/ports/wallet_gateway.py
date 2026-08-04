from abc import ABC, abstractmethod
from decimal import Decimal


class WalletGateway(ABC):
    """Outbound port for reserving and releasing trader funds/holdings."""

    @abstractmethod
    async def reserve_for_buy(
        self,
        trader_id: str,
        amount: Decimal,
        currency: str,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def reserve_for_sell(
        self,
        trader_id: str,
        instrument_id: str,
        quantity: int,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def release_buy_reservation(
        self,
        trader_id: str,
        amount: Decimal,
        currency: str,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def release_sell_reservation(
        self,
        trader_id: str,
        instrument_id: str,
        quantity: int,
    ) -> None:
        raise NotImplementedError
