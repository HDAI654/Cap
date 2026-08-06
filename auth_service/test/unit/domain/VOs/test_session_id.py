import pytest
from src.domain.value_objects.session_id import SessionId
from src.exceptions import InvalidSessionIdError


def test_generate_roundtrip() -> None:
    sid = SessionId.generate()
    assert SessionId(sid.value) == sid


def test_rejects_invalid() -> None:
    with pytest.raises(InvalidSessionIdError):
        SessionId("bad")


def test_rejects_empty() -> None:
    with pytest.raises(InvalidSessionIdError):
        SessionId("  ")
