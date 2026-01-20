import pytest
from datetime import datetime
from auth_app.domain.value_objects.datetime import DateTime


class TestDevice:
    def test_not_str_datetime(self):
        with pytest.raises(ValueError):
            DateTime(25)
            DateTime(None)

    def test_empty_str_datetime(self):
        with pytest.raises(ValueError):
            DateTime("")
            DateTime(" ")
            DateTime("  ")

    def test_eq_datetime(self):
        dt = DateTime("2009-03-08")
        dt2 = DateTime("2009-03-08")
        dt3 = datetime(year=2009, month=3, day=8).isoformat()

        assert dt == dt2
        assert dt == dt3 and dt2 == dt3
