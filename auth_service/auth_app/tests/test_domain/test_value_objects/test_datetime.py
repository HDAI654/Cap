import pytest
from datetime import datetime, timezone
from auth_app.domain.value_objects.datetime import DateTime


class TestDevice:
    def test_none_datetime_auto_use_current_time(self):
        dt = DateTime(None)
        assert dt.value != None and isinstance(dt.value, float)

    def test_not_float_or_int_datetime(self):
        with pytest.raises(TypeError):
            DateTime("25")
            DateTime(["M", 25])

    def test_zero_and_negative_datetime(self):
        with pytest.raises(ValueError):
            DateTime(0)
            DateTime(-1)

    def test_int_datetime_auto_convert_to_float(self):
        dt = DateTime(1236457800.0)
        dt2 = DateTime(1236457800)
        assert dt.value == dt2.value

    def test_eq_datetime(self):
        dt = DateTime(1245542400.0)
        dt2 = DateTime(1245542400.0)
        dt3 = datetime(year=2009, month=6, day=21, tzinfo=timezone.utc).timestamp()

        assert dt == dt2
        assert dt == dt3 and dt2 == dt3
