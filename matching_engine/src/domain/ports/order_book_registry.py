from abc import ABC, abstractmethod

from src.domain.entities.order_book import OrderBook
from src.domain.value_objects.instrument_id import InstrumentId


class OrderBookRegistry(ABC):
    """Provides the in-memory order book for a given instrument."""

    @abstractmethod
    def get_or_create(self, instrument_id: InstrumentId) -> OrderBook:
        raise NotImplementedError

    @abstractmethod
    def get(self, instrument_id: InstrumentId) -> OrderBook | None:
        raise NotImplementedError
