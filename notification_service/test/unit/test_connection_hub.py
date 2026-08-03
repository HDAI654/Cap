from unittest.mock import AsyncMock

from src.domain.connection_hub import ConnectionHub


async def test_connect_and_send() -> None:
    hub = ConnectionHub()
    ws = AsyncMock()
    ws.send_json = AsyncMock()

    await hub.connect("trader-1", ws)
    assert hub.connected_trader_count() == 1

    sent = await hub.send_to_traders(
        ["trader-1"],
        {"event_type": "OrderOpened", "payload": {}},
    )
    assert sent == 1
    ws.send_json.assert_awaited_once()


async def test_multiple_sockets_same_trader() -> None:
    hub = ConnectionHub()
    ws1 = AsyncMock()
    ws1.send_json = AsyncMock()
    ws2 = AsyncMock()
    ws2.send_json = AsyncMock()

    await hub.connect("trader-1", ws1)
    await hub.connect("trader-1", ws2)
    assert hub.connected_trader_count() == 1

    sent = await hub.send_to_traders(
        ["trader-1"],
        {"event_type": "X", "payload": {}},
    )
    assert sent == 2


async def test_send_to_unknown_trader() -> None:
    hub = ConnectionHub()
    sent = await hub.send_to_traders(["nobody"], {"event_type": "X", "payload": {}})
    assert sent == 0


async def test_disconnect_removes_socket() -> None:
    hub = ConnectionHub()
    ws = AsyncMock()
    await hub.connect("trader-1", ws)
    await hub.disconnect("trader-1", ws)
    assert hub.connected_trader_count() == 0


async def test_stale_socket_is_removed_on_send_failure() -> None:
    hub = ConnectionHub()
    good = AsyncMock()
    good.send_json = AsyncMock()
    bad = AsyncMock()
    bad.send_json = AsyncMock(side_effect=RuntimeError("gone"))

    await hub.connect("trader-1", good)
    await hub.connect("trader-1", bad)

    sent = await hub.send_to_traders(
        ["trader-1"],
        {"event_type": "X", "payload": {}},
    )
    assert sent == 1
    sent_again = await hub.send_to_traders(
        ["trader-1"],
        {"event_type": "Y", "payload": {}},
    )
    assert sent_again == 1
