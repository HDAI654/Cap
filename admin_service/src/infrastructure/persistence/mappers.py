from src.domain.entities.instrument import Instrument
from src.domain.value_objects.currency import Currency
from src.domain.value_objects.instrument_id import InstrumentId
from src.domain.value_objects.instrument_status import InstrumentStatus
from src.domain.value_objects.money import Money
from src.domain.value_objects.quantity import Quantity
from src.infrastructure.persistence.models import InstrumentModel


def instrument_to_model(instrument: Instrument) -> InstrumentModel:
    return InstrumentModel(
        id=instrument.id.value,
        symbol=instrument.symbol,
        name=instrument.name,
        tick_size=instrument.tick_size.amount,
        tick_size_currency=instrument.tick_size.currency.value,
        lot_size=instrument.lot_size.value,
        minimum_order_quantity=instrument.minimum_order_quantity.value,
        maximum_order_quantity=instrument.maximum_order_quantity.value,
        currency=instrument.currency.value,
        total_shares=instrument.total_shares.value,
        status=instrument.status.value,
        created_at=instrument.created_at,
        updated_at=instrument.updated_at,
    )


def model_to_instrument(model: InstrumentModel) -> Instrument:
    currency = Currency(model.currency)
    return Instrument(
        id=InstrumentId(model.id),
        symbol=model.symbol,
        name=model.name,
        tick_size=Money(model.tick_size, Currency(model.tick_size_currency)),
        lot_size=Quantity(model.lot_size),
        minimum_order_quantity=Quantity(model.minimum_order_quantity),
        maximum_order_quantity=Quantity(model.maximum_order_quantity),
        currency=currency,
        total_shares=Quantity(model.total_shares),
        status=InstrumentStatus(model.status),
        created_at=model.created_at,
        updated_at=model.updated_at,
    )
