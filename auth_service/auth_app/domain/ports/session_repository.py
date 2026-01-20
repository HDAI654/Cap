from abc import ABC, abstractmethod
from typing import List
from auth_app.domain.entities.session import SessionEntity
from auth_app.domain.value_objects.id import ID


class SessionRepository(ABC):
    """Repository interface for Session entities."""

    @abstractmethod
    def __init__(self, redis_client):
        self.redis_client = redis_client

    @abstractmethod
    def add(self, session: SessionEntity) -> SessionEntity:
        """Create a new session in the database."""
        pass

    @abstractmethod
    def delete(self, id: ID, user_id: ID) -> None:
        """Delete a session."""
        pass

    @abstractmethod
    def get_by_id(self, id: ID) -> SessionEntity:
        """Get a session by ID."""
        pass

    @abstractmethod
    def get_by_user_id(self, user_id: ID) -> List[SessionEntity]:
        """Get a session by UserID."""
        pass
