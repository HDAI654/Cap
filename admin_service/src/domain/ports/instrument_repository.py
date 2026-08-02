from abc import ABC, abstractmethod

from src.domain.entities.instrument import Instrument
from src.domain.value_objects.instrument_id import InstrumentId


class InstrumentRepository(ABC):
    """Persistence port for Instrument aggregates."""

    @abstractmethod
    async def add(self, instrument: Instrument) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, instrument_id: InstrumentId) -> Instrument:
        raise NotImplementedError

    @abstractmethod
    async def get_by_symbol(self, symbol: str) -> Instrument | None:
        raise NotImplementedError

    @abstractmethod
    async def update(self, instrument: Instrument) -> None:
        raise NotImplementedError

    @abstractmethod
    async def list_all(self) -> list[Instrument]:
        raise NotImplementedError
