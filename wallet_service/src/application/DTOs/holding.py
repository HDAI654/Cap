from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class HoldingDTO:
    """Holding projection for the application boundary."""

    instrument_id: str
    available: int
    reserved: int
    average_cost: Decimal
    average_cost_currency: str
