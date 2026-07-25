import pytest
import uuid
from wallet_service.src.domain.value_objects.instrument_id import InstrumentId


class TestInstrumentId:
    def test_valid_instrument_id(self):
        id = str(uuid.uuid4())
        instrument_id = InstrumentId(id)
        assert instrument_id.value == id

    def test_instrument_id_as_string(self):
        id = str(uuid.uuid4())
        instrument_id = InstrumentId(id)
        assert str(instrument_id) == id

    def test_instrument_id_equality(self):
        id = str(uuid.uuid4())
        id1 = InstrumentId(id)
        id2 = InstrumentId(id)
        id3 = InstrumentId(str(uuid.uuid4()))

        assert id1 == id2
        assert id1 != id3
        assert hash(id1) == hash(id2)
