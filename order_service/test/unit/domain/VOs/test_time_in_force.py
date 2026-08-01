import pytest
from src.domain.value_objects.time_in_force import TimeInForce


class TestTimeInForce:
    def test_time_in_force_values(self):
        assert TimeInForce.GTC == "GTC"
        assert TimeInForce.IOC == "IOC"
        assert TimeInForce.FOK == "FOK"
        assert TimeInForce.DAY == "DAY"

    def test_time_in_force_from_string(self):
        assert TimeInForce("GTC") == TimeInForce.GTC
        assert TimeInForce("IOC") == TimeInForce.IOC
        assert TimeInForce("FOK") == TimeInForce.FOK
        assert TimeInForce("DAY") == TimeInForce.DAY

    def test_invalid_time_in_force(self):
        with pytest.raises(ValueError):
            TimeInForce("GTD")
