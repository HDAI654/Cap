from shared.id_vo import ID
from src.exceptions import InvalidInstrumentIdError


class InstrumentId(ID):
    """Unique identifier of a tradable instrument."""

    def __init__(self, value: str) -> None:
        super().__init__(value, InvalidInstrumentIdError)
