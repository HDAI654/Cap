from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from src.application.create_instrument import (
    CreateInstrumentCommand,
    CreateInstrumentHandler,
)
from src.domain.entities.instrument import Instrument
from src.exceptions import InstrumentAlreadyExistsError


async def test_creates_instrument(
    mock_uow: AsyncMock,
    mock_instrument_repository: AsyncMock,
) -> None:
    mock_instrument_repository.get_by_symbol.return_value = None

    result = await CreateInstrumentHandler(mock_uow).handle(
        CreateInstrumentCommand(
            symbol="aapl",
            name="Apple Inc.",
            tick_size=Decimal("0.01"),
            lot_size=1,
            minimum_order_quantity=1,
            maximum_order_quantity=10000,
            currency="USD",
            total_shares=0,
        )
    )

    assert result.instrument_id
    mock_instrument_repository.add.assert_awaited_once()
    added: Instrument = mock_instrument_repository.add.await_args.args[0]
    assert added.symbol == "AAPL"
    mock_uow.commit.assert_awaited_once()


async def test_duplicate_symbol_raises(
    mock_uow: AsyncMock,
    mock_instrument_repository: AsyncMock,
    sample_instrument: Instrument,
) -> None:
    mock_instrument_repository.get_by_symbol.return_value = sample_instrument

    with pytest.raises(InstrumentAlreadyExistsError):
        await CreateInstrumentHandler(mock_uow).handle(
            CreateInstrumentCommand(
                symbol="AAPL",
                name="Apple Inc.",
                tick_size=Decimal("0.01"),
                lot_size=1,
                minimum_order_quantity=1,
                maximum_order_quantity=10000,
                currency="USD",
            )
        )

    mock_instrument_repository.add.assert_not_awaited()
