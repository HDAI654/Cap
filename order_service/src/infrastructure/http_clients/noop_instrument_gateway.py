from src.domain.ports.instrument_gateway import InstrumentGateway


class NoOpInstrumentGateway(InstrumentGateway):
    """Accepts all instruments when ADMIN integration is disabled."""

    async def ensure_tradable(self, instrument_id: str) -> None:
        return None
