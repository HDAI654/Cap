from unittest.mock import AsyncMock

import pytest

from src.application.activate_instrument import (
    ActivateInstrumentCommand,
    ActivateInstrumentHandler,
)
from src.domain.entities.instrument import Instrument
from src.domain.value_objects.instrument_status import InstrumentStatus
from src.exceptions import InvalidInstrumentStateError


async def test_activates_pending_instrument(
    mock_uow: AsyncMock,
    mock_instrument_repository: AsyncMock,
    sample_instrument: Instrument,
) -> None:
    mock_instrument_repository.get_by_id.return_value = sample_instrument

    await ActivateInstrumentHandler(mock_uow).handle(
        ActivateInstrumentCommand(instrument_id=sample_instrument.id.value)
    )

    assert sample_instrument.status is InstrumentStatus.ACTIVE
    mock_instrument_repository.update.assert_awaited_once_with(sample_instrument)
    mock_uow.commit.assert_awaited_once()


async def test_activates_halted_instrument(
    mock_uow: AsyncMock,
    mock_instrument_repository: AsyncMock,
    sample_instrument: Instrument,
) -> None:
    sample_instrument.activate()
    sample_instrument.halt()
    sample_instrument.clear_changes()
    mock_instrument_repository.get_by_id.return_value = sample_instrument

    await ActivateInstrumentHandler(mock_uow).handle(
        ActivateInstrumentCommand(instrument_id=sample_instrument.id.value)
    )

    assert sample_instrument.status is InstrumentStatus.ACTIVE
    mock_uow.commit.assert_awaited_once()


async def test_raises_when_already_active(
    mock_uow: AsyncMock,
    mock_instrument_repository: AsyncMock,
    sample_instrument: Instrument,
) -> None:
    sample_instrument.activate()
    sample_instrument.clear_changes()
    mock_instrument_repository.get_by_id.return_value = sample_instrument

    with pytest.raises(InvalidInstrumentStateError):
        await ActivateInstrumentHandler(mock_uow).handle(
            ActivateInstrumentCommand(instrument_id=sample_instrument.id.value)
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
        await ActivateInstrumentHandler(mock_uow).handle(
            ActivateInstrumentCommand(instrument_id=sample_instrument.id.value)
        )
