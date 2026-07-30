import uuid
from collections.abc import Iterator
import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def trader_id() -> str:
    """Fresh UUID v4 trader identifier."""
    return str(uuid.uuid4())


@pytest.fixture
def instrument_id() -> str:
    """Fresh UUID v4 instrument identifier."""
    return str(uuid.uuid4())


@pytest.fixture
def created_wallet(client: TestClient, trader_id: str) -> dict[str, str]:
    """Create a wallet and return ``{\"wallet_id\", \"trader_id\"}``."""
    response = client.post(
        "/api/v1/wallets",
        json={"trader_id": trader_id},
    )
    assert response.status_code == 201, response.text
    wallet_id = response.json()["wallet_id"]
    return {"wallet_id": wallet_id, "trader_id": trader_id}
