import pytest
from src.domain.value_objects.user_id import UserId
from src.exceptions import InvalidUserIdError


def test_generate_is_uuid_v4() -> None:
    uid = UserId.generate()
    assert len(uid.value) == 36
    assert UserId(uid.value) == uid


def test_rejects_empty() -> None:
    with pytest.raises(InvalidUserIdError):
        UserId("")


def test_rejects_non_uuid() -> None:
    with pytest.raises(InvalidUserIdError):
        UserId("not-a-uuid")


def test_rejects_non_string() -> None:
    with pytest.raises(InvalidUserIdError):
        UserId(123)  # type: ignore[arg-type]


def test_equality() -> None:
    a = UserId.generate()
    b = UserId(a.value)
    assert a == b
    assert hash(a) == hash(b)
