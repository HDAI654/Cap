from shared.id_vo import ID
from src.exceptions import InvalidInstrumentIdError


class InstrumentId(ID):
    """Represents the unique identifier of an Instrument."""

    def __init__(self, value: str) -> None:
        super().__init__(value, InvalidInstrumentIdError)
