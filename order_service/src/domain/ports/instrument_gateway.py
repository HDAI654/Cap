from abc import ABC, abstractmethod


class InstrumentGateway(ABC):
    """Outbound port for instrument status checks (Admin / store)."""

    @abstractmethod
    async def ensure_tradable(self, instrument_id: str) -> None:
        """Raise if the instrument cannot be traded (missing/halted/delisted)."""

        raise NotImplementedError
