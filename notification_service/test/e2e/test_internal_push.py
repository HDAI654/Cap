from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from src.app import app


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "NotificationService"
    assert "connected_traders" in body


def test_push_with_no_connected_traders(client: TestClient) -> None:
    response = client.post(
        "/internal/v1/notifications",
        json={
            "event_type": "OrderSubmitted",
            "recipient_trader_ids": ["11111111-1111-4111-8111-111111111111"],
            "payload": {"order_id": "o1"},
        },
    )
    assert response.status_code == 202
    assert response.json()["delivered"] == 0


def test_push_validation_empty_recipients(client: TestClient) -> None:
    response = client.post(
        "/internal/v1/notifications",
        json={
            "event_type": "OrderSubmitted",
            "recipient_trader_ids": [],
            "payload": {},
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_push_delivers_to_connected_socket(client: TestClient) -> None:
    hub = app.state.connection_hub
    ws = AsyncMock()
    ws.send_json = AsyncMock()

    await hub.connect("11111111-1111-4111-8111-111111111111", ws)

    response = client.post(
        "/internal/v1/notifications",
        json={
            "event_type": "OrderOpened",
            "recipient_trader_ids": ["11111111-1111-4111-8111-111111111111"],
            "payload": {"order_id": "o1"},
        },
    )
    assert response.status_code == 202
    assert response.json()["delivered"] == 1
    ws.send_json.assert_awaited()
