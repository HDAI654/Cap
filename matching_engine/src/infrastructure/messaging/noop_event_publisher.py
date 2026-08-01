import logging

from src.domain.events.matching_events import DomainEvent
from src.domain.ports.event_publisher import EventPublisher

logger = logging.getLogger(__name__)


class NoOpEventPublisher(EventPublisher):
    async def publish(self, event: DomainEvent) -> None:
        logger.debug("NoOpEventPublisher: dropping event_type=%s", event.event_type)
