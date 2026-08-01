from enum import StrEnum


class OrderType(StrEnum):
    """Execution style of an order."""

    MARKET = "MARKET"
    LIMIT = "LIMIT"
