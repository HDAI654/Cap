from dataclasses import dataclass
from datetime import datetime
from src.domain.value_objects.instrument_id import InstrumentId
from src.domain.value_objects.money import Money
from src.domain.value_objects.order_id import OrderId
from src.domain.value_objects.order_side import OrderSide
from src.domain.value_objects.order_type import OrderType
from src.domain.value_objects.quantity import Quantity
from src.domain.value_objects.time_in_force import TimeInForce
from src.domain.value_objects.trader_id import TraderId


@dataclass(slots=True)
class RestingOrder:
    """An order (or residual) resting on the book at a price level.

    Mutable only via ``reduce`` so the book can apply partial fills in place.
    """

    order_id: OrderId
    trader_id: TraderId
    instrument_id: InstrumentId
    side: OrderSide
    order_type: OrderType
    time_in_force: TimeInForce
    price: Money
    remaining_quantity: Quantity
    sequence: int
    accepted_at: datetime

    def reduce(self, quantity: Quantity) -> None:
        """Decrease remaining quantity after a fill."""
        self.remaining_quantity = self.remaining_quantity - quantity

    @property
    def is_depleted(self) -> bool:
        return self.remaining_quantity.value == 0
