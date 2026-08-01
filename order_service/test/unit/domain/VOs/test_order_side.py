import pytest
from src.domain.value_objects.order_side import OrderSide


class TestOrderSide:
    def test_order_side_values(self):
        assert OrderSide.BUY == "BUY"
        assert OrderSide.SELL == "SELL"

    def test_order_side_from_string(self):
        assert OrderSide("BUY") == OrderSide.BUY
        assert OrderSide("SELL") == OrderSide.SELL

    def test_invalid_order_side(self):
        with pytest.raises(ValueError):
            OrderSide("HOLD")
