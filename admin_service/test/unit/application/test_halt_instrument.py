from unittest.mock import AsyncMock

import pytest

from src.application.halt_instrument import HaltInstrumentCommand, HaltInstrumentHandler
from src.domain.entities.instrument import Instrument
from src.domain.value_objects.instrument_status import InstrumentStatus
from src.exceptions import InvalidInstrumentStateError


async def test_halts_active_instrument(
    mock_uow: AsyncMock,
    mock_instrument_repository: AsyncMock,
    sample_instrument: Instrument,
) -> None:
    sample_instrument.activate()
    sample_instrument.clear_changes()
    mock_instrument_repository.get_by_id.return_value = sample_instrument

    await HaltInstrumentHandler(mock_uow).handle(
        HaltInstrumentCommand(instrument_id=sample_instrument.id.value)
    )

    assert sample_instrument.status is InstrumentStatus.HALTED
    mock_instrument_repository.update.assert_awaited_once_with(sample_instrument)
    mock_uow.commit.assert_awaited_once()


async def test_raises_when_pending(
    mock_uow: AsyncMock,
    mock_instrument_repository: AsyncMock,
    sample_instrument: Instrument,
) -> None:
    mock_instrument_repository.get_by_id.return_value = sample_instrument

    with pytest.raises(InvalidInstrumentStateError):
        await HaltInstrumentHandler(mock_uow).handle(
            HaltInstrumentCommand(instrument_id=sample_instrument.id.value)
        )

    mock_instrument_repository.update.assert_not_awaited()
    mock_uow.commit.assert_not_awaited()


async def test_raises_when_already_halted(
    mock_uow: AsyncMock,
    mock_instrument_repository: AsyncMock,
    sample_instrument: Instrument,
) -> None:
    sample_instrument.activate()
    sample_instrument.halt()
    sample_instrument.clear_changes()
    mock_instrument_repository.get_by_id.return_value = sample_instrument

    with pytest.raises(InvalidInstrumentStateError):
        await HaltInstrumentHandler(mock_uow).handle(
            HaltInstrumentCommand(instrument_id=sample_instrument.id.value)
        )
