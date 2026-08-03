import asyncio
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionHub:
    """In-process registry of trader WebSocket connections."""

    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, trader_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections.setdefault(trader_id, set()).add(websocket)
        logger.info("WebSocket connected: trader_id=%s", trader_id)

    async def disconnect(self, trader_id: str, websocket: WebSocket) -> None:
        async with self._lock:
            sockets = self._connections.get(trader_id)
            if not sockets:
                return
            sockets.discard(websocket)
            if not sockets:
                del self._connections[trader_id]
        logger.info("WebSocket disconnected: trader_id=%s", trader_id)

    async def send_to_traders(
        self,
        trader_ids: list[str],
        message: dict[str, Any],
    ) -> int:
        """Fan-out JSON message to all sockets of the given traders.

        Returns the number of successful sends.
        """
        sent = 0
        async with self._lock:
            targets: list[tuple[str, WebSocket]] = []
            for trader_id in trader_ids:
                for ws in self._connections.get(trader_id, set()):
                    targets.append((trader_id, ws))

        stale: list[tuple[str, WebSocket]] = []
        for trader_id, ws in targets:
            try:
                await ws.send_json(message)
                sent += 1
            except Exception:
                logger.warning(
                    "Failed to send to trader_id=%s — marking stale",
                    trader_id,
                )
                stale.append((trader_id, ws))

        for trader_id, ws in stale:
            await self.disconnect(trader_id, ws)

        return sent

    def connected_trader_count(self) -> int:
        return len(self._connections)
