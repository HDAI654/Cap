import logging
from typing import Any

import httpx

from src.domain.ports.notification_gateway import NotificationGateway
from src.exceptions import NotificationPushError

logger = logging.getLogger(__name__)


class HttpNotificationGateway(NotificationGateway):
    """Push notifications to Notification Service via internal HTTP API."""

    def __init__(self, base_url: str, push_path: str, timeout: float = 5.0) -> None:
        self._url = base_url.rstrip("/") + push_path
        self._timeout = timeout

    async def push(
        self,
        *,
        event_type: str,
        recipient_trader_ids: list[str],
        payload: dict[str, Any],
    ) -> None:
        body = {
            "event_type": event_type,
            "recipient_trader_ids": recipient_trader_ids,
            "payload": payload,
        }
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(self._url, json=body)
                response.raise_for_status()
            logger.info(
                "Pushed event_type=%s to NS recipients=%s",
                event_type,
                recipient_trader_ids,
            )
        except Exception as exc:
            logger.exception("Failed to push notification to NS")
            raise NotificationPushError(
                f"Failed to push '{event_type}' to Notification Service: {exc}"
            ) from exc
