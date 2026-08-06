from datetime import date
import pytest
from src.domain.value_objects.date import Date
from src.exceptions import InvalidDateError


def test_from_iso_string() -> None:
    assert Date("2026-08-01").value == date(2026, 8, 1)


def test_from_date_object() -> None:
    assert Date(date(2026, 1, 2)).value == date(2026, 1, 2)


def test_rejects_invalid_string() -> None:
    with pytest.raises(InvalidDateError):
        Date("not-a-date")
