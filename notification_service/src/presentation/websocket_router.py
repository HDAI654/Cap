import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/v1/notifications/{trader_id}")
async def trader_notifications(websocket: WebSocket, trader_id: str) -> None:
    """Trader WebSocket endpoint (Gateway upgrades and routes here).

    NOTE: Authentication is expected at the Gateway. This service trusts
    ``trader_id`` from the path after Gateway validation.
    """
    hub = websocket.app.state.connection_hub
    await hub.connect(trader_id, websocket)
    try:
        while True:
            # Keep-alive / client pings; payload ignored.
            await websocket.receive_text()
    except WebSocketDisconnect:
        await hub.disconnect(trader_id, websocket)
    except Exception:
        logger.exception("WebSocket error trader_id=%s", trader_id)
        await hub.disconnect(trader_id, websocket)
