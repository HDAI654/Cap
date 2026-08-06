import pytest
from src.domain.value_objects.password import Password
from src.exceptions import InvalidPasswordError


def test_accepts_strong_password() -> None:
    assert Password("Secret12").value == "Secret12"


def test_rejects_too_short() -> None:
    with pytest.raises(InvalidPasswordError):
        Password("Ab1")


def test_rejects_no_digit() -> None:
    with pytest.raises(InvalidPasswordError):
        Password("NoDigitsHere")


def test_rejects_no_letter() -> None:
    with pytest.raises(InvalidPasswordError):
        Password("12345678")


def test_rejects_non_string() -> None:
    with pytest.raises(InvalidPasswordError):
        Password(None)  # type: ignore[arg-type]
