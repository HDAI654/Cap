from unittest.mock import AsyncMock

import pytest

from src.application.delist_instrument import (
    DelistInstrumentCommand,
    DelistInstrumentHandler,
)
from src.domain.entities.instrument import Instrument
from src.domain.value_objects.instrument_status import InstrumentStatus
from src.exceptions import InvalidInstrumentStateError


async def test_delists_pending_instrument(
    mock_uow: AsyncMock,
    mock_instrument_repository: AsyncMock,
    sample_instrument: Instrument,
) -> None:
    mock_instrument_repository.get_by_id.return_value = sample_instrument

    await DelistInstrumentHandler(mock_uow).handle(
        DelistInstrumentCommand(instrument_id=sample_instrument.id.value)
    )

    assert sample_instrument.status is InstrumentStatus.DELISTED
    mock_instrument_repository.update.assert_awaited_once_with(sample_instrument)
    mock_uow.commit.assert_awaited_once()


async def test_delists_active_instrument(
    mock_uow: AsyncMock,
    mock_instrument_repository: AsyncMock,
    sample_instrument: Instrument,
) -> None:
    sample_instrument.activate()
    sample_instrument.clear_changes()
    mock_instrument_repository.get_by_id.return_value = sample_instrument

    await DelistInstrumentHandler(mock_uow).handle(
        DelistInstrumentCommand(instrument_id=sample_instrument.id.value)
    )

    assert sample_instrument.status is InstrumentStatus.DELISTED
    mock_uow.commit.assert_awaited_once()


async def test_raises_when_already_delisted(
    mock_uow: AsyncMock,
    mock_instrument_repository: AsyncMock,
    sample_instrument: Instrument,
) -> None:
    sample_instrument.delist()
    sample_instrument.clear_changes()
    mock_instrument_repository.get_by_id.return_value = sample_instrument

    with pytest.raises(InvalidInstrumentStateError):
        await DelistInstrumentHandler(mock_uow).handle(
            DelistInstrumentCommand(instrument_id=sample_instrument.id.value)
        )

    mock_instrument_repository.update.assert_not_awaited()
    mock_uow.commit.assert_not_awaited()
