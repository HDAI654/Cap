import pytest
from src.domain.value_objects.email import Email
from src.exceptions import InvalidEmailError


def test_normalizes_case_and_space() -> None:
    assert Email("  Foo@Bar.COM ").value == "foo@bar.com"


def test_accepts_valid() -> None:
    assert Email("a@b.co").value == "a@b.co"


def test_rejects_missing_at() -> None:
    with pytest.raises(InvalidEmailError):
        Email("not-an-email")


def test_rejects_empty() -> None:
    with pytest.raises(InvalidEmailError):
        Email("")


def test_rejects_too_long() -> None:
    with pytest.raises(InvalidEmailError):
        Email("a" * 250 + "@b.com")
