import re
from ...utils.crypto_utils import IDGenerator


def test_random_hex_default_length():
    value = IDGenerator.random_hex()

    # secrets.token_hex(n) returns a string of length 2 * n
    assert isinstance(value, str)
    assert len(value) == 64
    assert re.fullmatch(r"[0-9a-f]+", value)


def test_random_hex_custom_length():
    value = IDGenerator.random_hex(16)

    assert isinstance(value, str)
    assert len(value) == 32
    assert re.fullmatch(r"[0-9a-f]+", value)


def test_random_hex_uniqueness():
    values = {IDGenerator.random_hex() for _ in range(100)}

    # Extremely low collision probability
    assert len(values) == 100


def test_uuid4_format():
    value = IDGenerator.uuid4()

    assert isinstance(value, str)
    assert len(value) == 32
    assert re.fullmatch(r"[0-9a-f]{32}", value)


def test_uuid4_uniqueness():
    values = {IDGenerator.uuid4() for _ in range(100)}

    assert len(values) == 100
