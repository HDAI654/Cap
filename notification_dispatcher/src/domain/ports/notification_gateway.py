from abc import ABC, abstractmethod
from typing import Any


class NotificationGateway(ABC):
    """Outbound port: push a real-time notification to Notification Service."""

    @abstractmethod
    async def push(
        self,
        *,
        event_type: str,
        recipient_trader_ids: list[str],
        payload: dict[str, Any],
    ) -> None:
        raise NotImplementedError
