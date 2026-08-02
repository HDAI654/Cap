import time
import uuid
from collections.abc import Iterator
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

# Generate ephemeral RSA keypair for tests before app import reads Config.
_private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_private_pem = _private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption(),
).decode()
_public_pem = (
    _private_key.public_key()
    .public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    .decode()
)

import os

os.environ["AUTH_PUBLIC_KEY"] = _public_pem
os.environ["APP_ENV"] = "development"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

from src.app import app  # noqa: E402


def make_token(*, role: str = "ADMIN", expired: bool = False) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(uuid.uuid4()),
        "role": role,
        "iat": now,
        "exp": now + timedelta(hours=-1 if expired else 1),
    }
    return jwt.encode(payload, _private_pem, algorithm="RS256")


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def admin_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {make_token(role='ADMIN')}"}


@pytest.fixture
def trader_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {make_token(role='TRADER')}"}


@pytest.fixture
def instrument_payload() -> dict:
    return {
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "tick_size": "0.01",
        "lot_size": 1,
        "minimum_order_quantity": 1,
        "maximum_order_quantity": 10000,
        "currency": "USD",
        "total_shares": 0,
    }


@pytest.fixture
def expired_admin_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {make_token(role='ADMIN', expired=True)}"}
