from abc import ABC, abstractmethod

from src.domain.entities.order_history_entry import OrderHistoryEntry


class OrderHistoryRepository(ABC):
    @abstractmethod
    async def add(self, entry: OrderHistoryEntry) -> None:
        raise NotImplementedError

    @abstractmethod
    async def list_by_order(self, order_id: str) -> list[OrderHistoryEntry]:
        raise NotImplementedError

    @abstractmethod
    async def list_by_trader(self, trader_id: str) -> list[OrderHistoryEntry]:
        raise NotImplementedError
