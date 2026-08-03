from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.exceptions import NotificationPushError
from src.infrastructure.messaging.http_notification_gateway import (
    HttpNotificationGateway,
)
from src.infrastructure.messaging.noop_notification_gateway import (
    NoOpNotificationGateway,
)


async def test_http_gateway_posts_payload() -> None:
    gateway = HttpNotificationGateway(
        base_url="http://ns:8008",
        push_path="/internal/v1/notifications",
    )

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("httpx.AsyncClient", return_value=mock_client):
        await gateway.push(
            event_type="OrderSubmitted",
            recipient_trader_ids=["t1"],
            payload={"order_id": "o1"},
        )

    mock_client.post.assert_awaited_once()
    args, kwargs = mock_client.post.await_args
    assert args[0] == "http://ns:8008/internal/v1/notifications"
    assert kwargs["json"]["event_type"] == "OrderSubmitted"
    assert kwargs["json"]["recipient_trader_ids"] == ["t1"]


async def test_http_gateway_raises_on_http_error() -> None:
    gateway = HttpNotificationGateway(
        base_url="http://ns:8008",
        push_path="/internal/v1/notifications",
    )

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(side_effect=httpx.ConnectError("down"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(NotificationPushError):
            await gateway.push(
                event_type="OrderSubmitted",
                recipient_trader_ids=["t1"],
                payload={},
            )


async def test_noop_gateway_does_not_raise() -> None:
    gateway = NoOpNotificationGateway()
    await gateway.push(
        event_type="OrderSubmitted",
        recipient_trader_ids=["t1"],
        payload={"order_id": "o1"},
    )
