from abc import ABC, abstractmethod
from types import TracebackType
from typing import Self

from src.domain.ports.order_history_repository import OrderHistoryRepository
from src.domain.ports.trade_repository import TradeRepository


class UnitOfWork(ABC):
    trades: TradeRepository
    order_history: OrderHistoryRepository

    @abstractmethod
    async def __aenter__(self) -> Self:
        raise NotImplementedError

    @abstractmethod
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def commit(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def rollback(self) -> None:
        raise NotImplementedError
