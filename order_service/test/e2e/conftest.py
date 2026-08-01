import uuid
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from src.app import app


@pytest.fixture
def client() -> Iterator[TestClient]:
    """HTTP client with app lifespan (creates schema, disposes engine)."""
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
def limit_order_payload(trader_id: str, instrument_id: str) -> dict:
    return {
        "trader_id": trader_id,
        "instrument_id": instrument_id,
        "side": "BUY",
        "order_type": "LIMIT",
        "time_in_force": "GTC",
        "quantity": 100,
        "idempotency_key": f"e2e-limit-{uuid.uuid4()}",
        "limit_price": "10.50",
        "limit_price_currency": "USD",
    }


@pytest.fixture
def market_order_payload(trader_id: str, instrument_id: str) -> dict:
    return {
        "trader_id": trader_id,
        "instrument_id": instrument_id,
        "side": "SELL",
        "order_type": "MARKET",
        "time_in_force": "IOC",
        "quantity": 50,
        "idempotency_key": f"e2e-market-{uuid.uuid4()}",
    }


@pytest.fixture
def submitted_limit_order(
    client: TestClient,
    limit_order_payload: dict,
) -> dict:
    """Submit a LIMIT order and return payload plus order_id."""
    response = client.post("/api/v1/orders", json=limit_order_payload)
    assert response.status_code == 201, response.text
    return {
        **limit_order_payload,
        "order_id": response.json()["order_id"],
    }
