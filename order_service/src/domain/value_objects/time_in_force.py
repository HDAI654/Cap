from enum import StrEnum


class TimeInForce(StrEnum):
    """Duration policy that controls how long an order remains active."""

    GTC = "GTC"
    IOC = "IOC"
    FOK = "FOK"
    DAY = "DAY"
