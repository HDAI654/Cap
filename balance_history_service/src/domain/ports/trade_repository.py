from abc import ABC, abstractmethod

from src.domain.entities.trade_record import TradeRecord


class TradeRepository(ABC):
    @abstractmethod
    async def add(self, trade: TradeRecord) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, trade_id: str) -> TradeRecord:
        raise NotImplementedError

    @abstractmethod
    async def list_by_trader(self, trader_id: str) -> list[TradeRecord]:
        raise NotImplementedError

    @abstractmethod
    async def list_by_instrument(self, instrument_id: str) -> list[TradeRecord]:
        raise NotImplementedError

    @abstractmethod
    async def exists(self, trade_id: str) -> bool:
        raise NotImplementedError
