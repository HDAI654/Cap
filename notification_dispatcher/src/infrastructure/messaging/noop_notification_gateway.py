import logging
from typing import Any

from src.domain.ports.notification_gateway import NotificationGateway

logger = logging.getLogger(__name__)


class NoOpNotificationGateway(NotificationGateway):
    async def push(
        self,
        *,
        event_type: str,
        recipient_trader_ids: list[str],
        payload: dict[str, Any],
    ) -> None:
        logger.debug(
            "NoOpNotificationGateway: event_type=%s recipients=%s",
            event_type,
            recipient_trader_ids,
        )
