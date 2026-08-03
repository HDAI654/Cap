import logging
from dataclasses import dataclass
from typing import Any

from src.domain.connection_hub import ConnectionHub
from src.exceptions import InvalidNotificationError

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class DeliverNotificationCommand:
    event_type: str
    recipient_trader_ids: list[str]
    payload: dict[str, Any]


class DeliverNotificationHandler:
    """Deliver a notification from the Dispatcher to connected WebSocket clients."""

    def __init__(self, hub: ConnectionHub) -> None:
        self._hub = hub

    async def handle(self, command: DeliverNotificationCommand) -> int:
        if not command.event_type:
            raise InvalidNotificationError("event_type is required.")
        if not command.recipient_trader_ids:
            raise InvalidNotificationError("recipient_trader_ids must not be empty.")

        message = {
            "event_type": command.event_type,
            "payload": command.payload,
        }
        sent = await self._hub.send_to_traders(
            command.recipient_trader_ids,
            message,
        )
        logger.info(
            "Delivered event_type=%s recipients=%s sent=%s",
            command.event_type,
            command.recipient_trader_ids,
            sent,
        )
        return sent
