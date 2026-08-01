import pytest
from src.domain.value_objects.order_type import OrderType


class TestOrderType:
    def test_order_type_values(self):
        assert OrderType.MARKET == "MARKET"
        assert OrderType.LIMIT == "LIMIT"

    def test_order_type_from_string(self):
        assert OrderType("MARKET") == OrderType.MARKET
        assert OrderType("LIMIT") == OrderType.LIMIT

    def test_invalid_order_type(self):
        with pytest.raises(ValueError):
            OrderType("STOP")
