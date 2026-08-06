import pytest
from src.domain.value_objects.device import Device
from src.exceptions import InvalidDeviceError


def test_accepts_label() -> None:
    assert Device("iphone-15").value == "iphone-15"


def test_rejects_empty() -> None:
    with pytest.raises(InvalidDeviceError):
        Device("")


def test_rejects_too_long() -> None:
    with pytest.raises(InvalidDeviceError):
        Device("x" * 51)
