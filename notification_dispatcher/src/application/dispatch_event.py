import logging
from typing import Any

from src.domain.ports.notification_gateway import NotificationGateway

logger = logging.getLogger(__name__)


class DispatchEventHandler:
    """Map a bus event to recipient traders and push to Notification Service."""

    def __init__(self, gateway: NotificationGateway) -> None:
        self._gateway = gateway

    async def handle(self, event_type: str, payload: dict[str, Any]) -> None:
        recipients = self._resolve_recipients(event_type, payload)
        if not recipients:
            logger.debug(
                "No recipients for event_type=%s — skip push",
                event_type,
            )
            return

        logger.info(
            "Dispatching event_type=%s recipients=%s",
            event_type,
            recipients,
        )
        await self._gateway.push(
            event_type=event_type,
            recipient_trader_ids=recipients,
            payload=payload,
        )

    @staticmethod
    def _resolve_recipients(
        event_type: str, payload: dict[str, Any]
    ) -> list[str]:
        recipients: set[str] = set()

        if trader_id := payload.get("trader_id"):
            recipients.add(str(trader_id))
        if buyer_id := payload.get("buyer_id"):
            recipients.add(str(buyer_id))
        if seller_id := payload.get("seller_id"):
            recipients.add(str(seller_id))

        # Explicit empty strings are not valid recipients.
        return sorted(r for r in recipients if r)
