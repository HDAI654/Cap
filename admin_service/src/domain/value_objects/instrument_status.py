from enum import StrEnum


class InstrumentStatus(StrEnum):
    """Operational status of a listed instrument."""

    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    HALTED = "HALTED"
    DELISTED = "DELISTED"
