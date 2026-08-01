import pytest
from src.domain.value_objects.order_id import OrderId
from src.domain.value_objects.trader_id import TraderId
from src.domain.value_objects.instrument_id import InstrumentId
from src.exceptions import (
    InvalidOrderIdError,
    InvalidTraderIdError,
    InvalidInstrumentIdError,
)


class TestOrderId:
    def test_not_str(self):
        with pytest.raises(InvalidOrderIdError):
            OrderId(123)

        with pytest.raises(InvalidOrderIdError):
            OrderId(None)

        with pytest.raises(InvalidOrderIdError):
            OrderId(45.67)

    def test_empty_str(self):
        with pytest.raises(InvalidOrderIdError):
            OrderId("")

        with pytest.raises(InvalidOrderIdError):
            OrderId("   ")

    def test_invalid_uuid_format(self):
        invalid_uuids = [
            "not-a-uuid",
            "123e4567-e89b-12d3-a456-42661417400",
            "123e4567-e89b-12d3-a456-4266141740000",
            "123e4567-e89b-12d3-a456-42661417400x",
        ]
        for invalid in invalid_uuids:
            with pytest.raises(InvalidOrderIdError):
                OrderId(invalid)

    def test_valid_uuid_v4(self):
        valid = "3bb6a3ca-66dc-440e-8d11-d8cca7ad7792"
        order_id = OrderId(valid)
        assert order_id.value == valid

    def test_uuid_strip(self):
        raw = "    3bb6a3ca-66dc-440e-8d11-d8cca7ad7792    "
        order_id = OrderId(raw)
        assert order_id.value == raw.strip()

    def test_generate(self):
        order_id = OrderId.generate()
        assert isinstance(order_id, OrderId)
        assert len(order_id.value) == 36

    def test_generate_always_unique(self):
        ids = [OrderId.generate().value for _ in range(100)]
        assert len(ids) == len(set(ids))

    def test_equality(self):
        value = "3bb6a3ca-66dc-440e-8d11-d8cca7ad7792"
        assert OrderId(value) == OrderId(value)
        assert OrderId(value) != OrderId.generate()


class TestTraderId:
    def test_not_str(self):
        with pytest.raises(InvalidTraderIdError):
            TraderId(123)

    def test_empty_str(self):
        with pytest.raises(InvalidTraderIdError):
            TraderId("")

    def test_invalid_uuid_format(self):
        with pytest.raises(InvalidTraderIdError):
            TraderId("not-a-uuid")

    def test_valid_and_generate(self):
        valid = "3bb6a3ca-66dc-440e-8d11-d8cca7ad7792"
        trader_id = TraderId(valid)
        assert trader_id.value == valid

        generated = TraderId.generate()
        assert isinstance(generated, TraderId)
        assert len(generated.value) == 36


class TestInstrumentId:
    def test_not_str(self):
        with pytest.raises(InvalidInstrumentIdError):
            InstrumentId(123)

    def test_empty_str(self):
        with pytest.raises(InvalidInstrumentIdError):
            InstrumentId("")

    def test_invalid_uuid_format(self):
        with pytest.raises(InvalidInstrumentIdError):
            InstrumentId("not-a-uuid")

    def test_valid_and_generate(self):
        valid = "3bb6a3ca-66dc-440e-8d11-d8cca7ad7792"
        instrument_id = InstrumentId(valid)
        assert instrument_id.value == valid

        generated = InstrumentId.generate()
        assert isinstance(generated, InstrumentId)
        assert len(generated.value) == 36
