from abc import ABC, abstractmethod

from src.domain.events.order_events import DomainEvent


class EventPublisher(ABC):
    """Outbound port for publishing domain events to the event bus."""

    @abstractmethod
    async def publish(self, event: DomainEvent) -> None:
        """Publish a single domain event.

        Raises:
            MessagingError: If the event cannot be delivered to the bus.
        """
        raise NotImplementedError
