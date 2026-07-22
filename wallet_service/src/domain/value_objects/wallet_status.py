from enum import StrEnum


class WalletStatus(StrEnum):
    """Represents the operational status of a wallet."""

    ACTIVE = "ACTIVE"
    LOCKED = "LOCKED"
    CLOSED = "CLOSED"


WalletStatus.ACTIVE