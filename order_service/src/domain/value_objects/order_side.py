from enum import StrEnum


class OrderSide(StrEnum):
    """Direction of an order relative to the instrument."""

    BUY = "BUY"
    SELL = "SELL"
