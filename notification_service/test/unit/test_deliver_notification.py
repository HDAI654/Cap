from unittest.mock import AsyncMock

import pytest

from src.application.deliver_notification import (
    DeliverNotificationCommand,
    DeliverNotificationHandler,
)
from src.domain.connection_hub import ConnectionHub
from src.exceptions import InvalidNotificationError


async def test_delivers_to_hub() -> None:
    hub = AsyncMock(spec=ConnectionHub)
    hub.send_to_traders = AsyncMock(return_value=2)
    handler = DeliverNotificationHandler(hub)

    sent = await handler.handle(
        DeliverNotificationCommand(
            event_type="OrderFilled",
            recipient_trader_ids=["t1", "t2"],
            payload={"order_id": "o1"},
        )
    )

    assert sent == 2
    hub.send_to_traders.assert_awaited_once()
    args = hub.send_to_traders.await_args.args
    assert args[0] == ["t1", "t2"]
    assert args[1]["event_type"] == "OrderFilled"
    assert args[1]["payload"]["order_id"] == "o1"


async def test_empty_recipients_raises() -> None:
    hub = AsyncMock(spec=ConnectionHub)
    handler = DeliverNotificationHandler(hub)

    with pytest.raises(InvalidNotificationError):
        await handler.handle(
            DeliverNotificationCommand(
                event_type="OrderFilled",
                recipient_trader_ids=[],
                payload={},
            )
        )


async def test_empty_event_type_raises() -> None:
    hub = AsyncMock(spec=ConnectionHub)
    handler = DeliverNotificationHandler(hub)

    with pytest.raises(InvalidNotificationError):
        await handler.handle(
            DeliverNotificationCommand(
                event_type="",
                recipient_trader_ids=["t1"],
                payload={},
            )
        )
