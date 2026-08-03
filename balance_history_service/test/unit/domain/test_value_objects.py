import uuid

import pytest

from src.domain.value_objects.instrument_id import InstrumentId
from src.domain.value_objects.order_id import OrderId
from src.domain.value_objects.trade_id import TradeId
from src.domain.value_objects.trader_id import TraderId
from src.exceptions import (
    InvalidInstrumentIdError,
    InvalidOrderIdError,
    InvalidTradeIdError,
    InvalidTraderIdError,
)


def test_trade_id_generate_and_parse() -> None:
    generated = TradeId.generate()
    uuid.UUID(generated.value, version=4)
    assert TradeId(generated.value).value == generated.value


def test_trade_id_rejects_invalid() -> None:
    with pytest.raises(InvalidTradeIdError):
        TradeId("bad")


def test_order_id_rejects_invalid() -> None:
    with pytest.raises(InvalidOrderIdError):
        OrderId("")


def test_trader_id_rejects_invalid() -> None:
    with pytest.raises(InvalidTraderIdError):
        TraderId("not-uuid")


def test_instrument_id_accepts_uuid() -> None:
    value = str(uuid.uuid4())
    assert InstrumentId(value).value == value


def test_instrument_id_rejects_invalid() -> None:
    with pytest.raises(InvalidInstrumentIdError):
        InstrumentId("x")
