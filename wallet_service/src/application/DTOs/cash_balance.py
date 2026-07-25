from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class CashBalanceDTO:
    """Cash balance projection for the application boundary."""

    currency: str
    available: Decimal
    reserved: Decimal
