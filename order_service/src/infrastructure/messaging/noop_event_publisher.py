import logging

from src.domain.events.order_events import DomainEvent
from src.domain.ports.event_publisher import EventPublisher

logger = logging.getLogger(__name__)


class NoOpEventPublisher(EventPublisher):
    """Drops events; used when the event bus is disabled (dev / tests)."""

    async def publish(self, event: DomainEvent) -> None:
        logger.debug(
            "NoOpEventPublisher: dropping event_type=%s",
            event.event_type,
        )
