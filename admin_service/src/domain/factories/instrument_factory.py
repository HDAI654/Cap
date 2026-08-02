from src.domain.entities.instrument import Instrument
from src.domain.value_objects.currency import Currency
from src.domain.value_objects.money import Money
from src.domain.value_objects.quantity import Quantity


class InstrumentFactory:
    """Creates Instrument aggregates."""

    @staticmethod
    def create(
        symbol: str,
        name: str,
        tick_size: Money,
        lot_size: Quantity,
        minimum_order_quantity: Quantity,
        maximum_order_quantity: Quantity,
        currency: Currency,
        total_shares: Quantity | None = None,
    ) -> Instrument:
        return Instrument.create(
            symbol=symbol,
            name=name,
            tick_size=tick_size,
            lot_size=lot_size,
            minimum_order_quantity=minimum_order_quantity,
            maximum_order_quantity=maximum_order_quantity,
            currency=currency,
            total_shares=total_shares,
        )
