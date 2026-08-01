import pytest
from src.domain.value_objects.order_status import OrderStatus


class TestOrderStatus:
    def test_order_status_values(self):
        assert OrderStatus.NEW == "NEW"
        assert OrderStatus.OPEN == "OPEN"
        assert OrderStatus.PARTIALLY_FILLED == "PARTIALLY_FILLED"
        assert OrderStatus.FILLED == "FILLED"
        assert OrderStatus.CANCELLED == "CANCELLED"
        assert OrderStatus.REJECTED == "REJECTED"
        assert OrderStatus.EXPIRED == "EXPIRED"

    def test_order_status_from_string(self):
        assert OrderStatus("NEW") == OrderStatus.NEW
        assert OrderStatus("OPEN") == OrderStatus.OPEN
        assert OrderStatus("PARTIALLY_FILLED") == OrderStatus.PARTIALLY_FILLED
        assert OrderStatus("FILLED") == OrderStatus.FILLED
        assert OrderStatus("CANCELLED") == OrderStatus.CANCELLED
        assert OrderStatus("REJECTED") == OrderStatus.REJECTED
        assert OrderStatus("EXPIRED") == OrderStatus.EXPIRED

    def test_invalid_order_status(self):
        with pytest.raises(ValueError):
            OrderStatus("PENDING")
