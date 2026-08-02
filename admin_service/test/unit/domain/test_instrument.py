from decimal import Decimal

import pytest

from src.domain.entities.instrument import Instrument
from src.domain.value_objects.currency import Currency
from src.domain.value_objects.instrument_status import InstrumentStatus
from src.domain.value_objects.money import Money
from src.domain.value_objects.quantity import Quantity
from src.exceptions import InvalidInstrumentParametersError, InvalidInstrumentStateError


def _create(**overrides) -> Instrument:
    params = {
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "tick_size": Money(Decimal("0.01"), Currency.USD),
        "lot_size": Quantity(1),
        "minimum_order_quantity": Quantity(1),
        "maximum_order_quantity": Quantity(10000),
        "currency": Currency.USD,
        "total_shares": Quantity(0),
    }
    params.update(overrides)
    return Instrument.create(**params)


def test_create_pending_instrument() -> None:
    instrument = _create()
    assert instrument.status is InstrumentStatus.PENDING
    assert instrument.symbol == "AAPL"
    assert instrument.total_shares.value == 0


def test_symbol_is_normalized() -> None:
    instrument = _create(symbol="  aapl  ")
    assert instrument.symbol == "AAPL"


def test_activate_halt_delist_cycle() -> None:
    instrument = _create()
    instrument.activate()
    assert instrument.status is InstrumentStatus.ACTIVE

    instrument.halt()
    assert instrument.status is InstrumentStatus.HALTED

    instrument.activate()
    assert instrument.status is InstrumentStatus.ACTIVE

    instrument.delist()
    assert instrument.status is InstrumentStatus.DELISTED


def test_cannot_activate_delisted() -> None:
    instrument = _create()
    instrument.delist()
    with pytest.raises(InvalidInstrumentStateError):
        instrument.activate()


def test_cannot_halt_unless_active() -> None:
    instrument = _create()
    with pytest.raises(InvalidInstrumentStateError):
        instrument.halt()


def test_allocate_shares() -> None:
    instrument = _create()
    instrument.allocate_shares(Quantity(1000))
    assert instrument.total_shares.value == 1000
    instrument.allocate_shares(Quantity(500))
    assert instrument.total_shares.value == 1500


def test_allocate_zero_raises() -> None:
    instrument = _create()
    with pytest.raises(InvalidInstrumentParametersError):
        instrument.allocate_shares(Quantity(0))


def test_cannot_allocate_to_delisted() -> None:
    instrument = _create()
    instrument.delist()
    with pytest.raises(InvalidInstrumentStateError):
        instrument.allocate_shares(Quantity(10))


def test_invalid_max_lt_min() -> None:
    with pytest.raises(InvalidInstrumentParametersError):
        _create(
            minimum_order_quantity=Quantity(100),
            maximum_order_quantity=Quantity(10),
        )
