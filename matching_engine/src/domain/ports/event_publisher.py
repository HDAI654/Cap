from abc import ABC, abstractmethod

from src.domain.events.matching_events import DomainEvent


class EventPublisher(ABC):
    """Outbound port for publishing matching events to the event bus."""

    @abstractmethod
    async def publish(self, event: DomainEvent) -> None:
        raise NotImplementedError
