import pytest
from src.domain.value_objects.hashed_password import HashedPassword
from src.exceptions import InvalidHashedPasswordError


def test_accepts_non_empty() -> None:
    assert HashedPassword("$2b$12$abc").value == "$2b$12$abc"


def test_rejects_empty() -> None:
    with pytest.raises(InvalidHashedPasswordError):
        HashedPassword("   ")
