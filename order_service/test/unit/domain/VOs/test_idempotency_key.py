import pytest
from src.domain.value_objects.idempotency_key import IdempotencyKey
from src.exceptions import InvalidIdempotencyKeyError


class TestIdempotencyKey:
    def test_valid_key(self):
        key = IdempotencyKey("client-key-001")
        assert key.value == "client-key-001"

    def test_strips_whitespace(self):
        key = IdempotencyKey("  client-key-001  ")
        assert key.value == "client-key-001"

    def test_not_str(self):
        with pytest.raises(InvalidIdempotencyKeyError):
            IdempotencyKey(123)

        with pytest.raises(InvalidIdempotencyKeyError):
            IdempotencyKey(None)

    def test_empty_str(self):
        with pytest.raises(InvalidIdempotencyKeyError):
            IdempotencyKey("")

        with pytest.raises(InvalidIdempotencyKeyError):
            IdempotencyKey("   ")

    def test_max_length_allowed(self):
        value = "a" * IdempotencyKey.MAX_LENGTH
        key = IdempotencyKey(value)
        assert key.value == value

    def test_exceeds_max_length(self):
        value = "a" * (IdempotencyKey.MAX_LENGTH + 1)
        with pytest.raises(InvalidIdempotencyKeyError):
            IdempotencyKey(value)

    def test_equality(self):
        k1 = IdempotencyKey("same-key")
        k2 = IdempotencyKey("same-key")
        k3 = IdempotencyKey("other-key")

        assert k1 == k2
        assert k1 != k3

    def test_hash(self):
        k1 = IdempotencyKey("same-key")
        k2 = IdempotencyKey("same-key")
        assert hash(k1) == hash(k2)
