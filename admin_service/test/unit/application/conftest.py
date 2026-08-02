from unittest.mock import AsyncMock

import pytest

from src.domain.entities.instrument import Instrument
from src.domain.ports.instrument_repository import InstrumentRepository
from src.domain.ports.unit_of_work import UnitOfWork
from src.domain.value_objects.currency import Currency
from src.domain.value_objects.money import Money
from src.domain.value_objects.quantity import Quantity
from decimal import Decimal


@pytest.fixture
def mock_instrument_repository() -> AsyncMock:
    repo = AsyncMock(spec=InstrumentRepository)
    repo.add = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.get_by_symbol = AsyncMock()
    repo.update = AsyncMock()
    repo.list_all = AsyncMock()
    return repo


@pytest.fixture
def mock_uow(mock_instrument_repository: AsyncMock) -> AsyncMock:
    uow = AsyncMock(spec=UnitOfWork)
    uow.instruments = mock_instrument_repository
    uow.commit = AsyncMock()
    uow.rollback = AsyncMock()
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=None)
    return uow


@pytest.fixture
def sample_instrument() -> Instrument:
    instrument = Instrument.create(
        symbol="AAPL",
        name="Apple Inc.",
        tick_size=Money(Decimal("0.01"), Currency.USD),
        lot_size=Quantity(1),
        minimum_order_quantity=Quantity(1),
        maximum_order_quantity=Quantity(10000),
        currency=Currency.USD,
        total_shares=Quantity(0),
    )
    instrument.clear_changes()
    return instrument
