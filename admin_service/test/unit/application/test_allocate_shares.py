from unittest.mock import AsyncMock

import pytest

from src.application.allocate_shares import (
    AllocateSharesCommand,
    AllocateSharesHandler,
)
from src.domain.entities.instrument import Instrument
from src.domain.value_objects.quantity import Quantity
from src.exceptions import InvalidInstrumentParametersError, InvalidInstrumentStateError


async def test_allocates_shares(
    mock_uow: AsyncMock,
    mock_instrument_repository: AsyncMock,
    sample_instrument: Instrument,
) -> None:
    mock_instrument_repository.get_by_id.return_value = sample_instrument

    await AllocateSharesHandler(mock_uow).handle(
        AllocateSharesCommand(
            instrument_id=sample_instrument.id.value,
            quantity=1000,
        )
    )

    assert sample_instrument.total_shares.value == 1000
    mock_instrument_repository.update.assert_awaited_once_with(sample_instrument)
    mock_uow.commit.assert_awaited_once()


async def test_allocates_increments_existing(
    mock_uow: AsyncMock,
    mock_instrument_repository: AsyncMock,
    sample_instrument: Instrument,
) -> None:
    sample_instrument.allocate_shares(Quantity(500))
    sample_instrument.clear_changes()
    mock_instrument_repository.get_by_id.return_value = sample_instrument

    await AllocateSharesHandler(mock_uow).handle(
        AllocateSharesCommand(
            instrument_id=sample_instrument.id.value,
            quantity=250,
        )
    )

    assert sample_instrument.total_shares.value == 750
    mock_uow.commit.assert_awaited_once()


async def test_raises_when_quantity_zero(
    mock_uow: AsyncMock,
    mock_instrument_repository: AsyncMock,
    sample_instrument: Instrument,
) -> None:
    mock_instrument_repository.get_by_id.return_value = sample_instrument

    with pytest.raises(InvalidInstrumentParametersError):
        await AllocateSharesHandler(mock_uow).handle(
            AllocateSharesCommand(
                instrument_id=sample_instrument.id.value,
                quantity=0,
            )
        )

    mock_instrument_repository.update.assert_not_awaited()
    mock_uow.commit.assert_not_awaited()


async def test_raises_when_delisted(
    mock_uow: AsyncMock,
    mock_instrument_repository: AsyncMock,
    sample_instrument: Instrument,
) -> None:
    sample_instrument.delist()
    sample_instrument.clear_changes()
    mock_instrument_repository.get_by_id.return_value = sample_instrument

    with pytest.raises(InvalidInstrumentStateError):
        await AllocateSharesHandler(mock_uow).handle(
            AllocateSharesCommand(
                instrument_id=sample_instrument.id.value,
                quantity=100,
            )
        )
