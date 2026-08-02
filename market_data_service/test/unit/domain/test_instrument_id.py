import uuid

import pytest

from src.domain.value_objects.instrument_id import InstrumentId
from src.exceptions import InvalidInstrumentIdError


def test_generate_produces_valid_uuid() -> None:
    instrument_id = InstrumentId.generate()
    uuid.UUID(instrument_id.value, version=4)


def test_accepts_valid_uuid_string() -> None:
    value = str(uuid.uuid4())
    instrument_id = InstrumentId(value)
    assert instrument_id.value == value


def test_rejects_empty() -> None:
    with pytest.raises(InvalidInstrumentIdError):
        InstrumentId("")


def test_rejects_non_uuid() -> None:
    with pytest.raises(InvalidInstrumentIdError):
        InstrumentId("not-a-uuid")
