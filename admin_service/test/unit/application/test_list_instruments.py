from unittest.mock import AsyncMock

from src.application.list_instruments import ListInstrumentsHandler
from src.domain.entities.instrument import Instrument
from src.domain.value_objects.currency import Currency
from src.domain.value_objects.money import Money
from src.domain.value_objects.quantity import Quantity
from decimal import Decimal


async def test_returns_empty_list(
    mock_uow: AsyncMock,
    mock_instrument_repository: AsyncMock,
) -> None:
    mock_instrument_repository.list_all.return_value = []

    result = await ListInstrumentsHandler(mock_uow).handle()

    assert result == []
    mock_instrument_repository.list_all.assert_awaited_once()


async def test_returns_mapped_dtos(
    mock_uow: AsyncMock,
    mock_instrument_repository: AsyncMock,
    sample_instrument: Instrument,
) -> None:
    other = Instrument.create(
        symbol="MSFT",
        name="Microsoft",
        tick_size=Money(Decimal("0.01"), Currency.USD),
        lot_size=Quantity(1),
        minimum_order_quantity=Quantity(1),
        maximum_order_quantity=Quantity(5000),
        currency=Currency.USD,
    )
    other.clear_changes()
    mock_instrument_repository.list_all.return_value = [sample_instrument, other]

    result = await ListInstrumentsHandler(mock_uow).handle()

    assert len(result) == 2
    assert result[0].symbol == "AAPL"
    assert result[1].symbol == "MSFT"
