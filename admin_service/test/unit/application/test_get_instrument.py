from unittest.mock import AsyncMock

import pytest

from src.application.get_instrument import GetInstrumentHandler, GetInstrumentQuery
from src.domain.entities.instrument import Instrument
from src.exceptions import InstrumentNotFoundError


async def test_returns_dto(
    mock_uow: AsyncMock,
    mock_instrument_repository: AsyncMock,
    sample_instrument: Instrument,
) -> None:
    mock_instrument_repository.get_by_id.return_value = sample_instrument

    dto = await GetInstrumentHandler(mock_uow).handle(
        GetInstrumentQuery(instrument_id=sample_instrument.id.value)
    )

    assert dto.instrument_id == sample_instrument.id.value
    assert dto.symbol == "AAPL"
    assert dto.name == "Apple Inc."
    assert dto.status == sample_instrument.status.value
    assert dto.total_shares == 0
    assert dto.currency == "USD"
    mock_instrument_repository.get_by_id.assert_awaited_once()


async def test_raises_when_not_found(
    mock_uow: AsyncMock,
    mock_instrument_repository: AsyncMock,
    sample_instrument: Instrument,
) -> None:
    mock_instrument_repository.get_by_id.side_effect = InstrumentNotFoundError(
        "not found"
    )

    with pytest.raises(InstrumentNotFoundError):
        await GetInstrumentHandler(mock_uow).handle(
            GetInstrumentQuery(instrument_id=sample_instrument.id.value)
        )
