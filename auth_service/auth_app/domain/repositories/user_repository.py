from abc import ABC, abstractmethod
from auth_app.domain.entities.user import UserEntity
from auth_app.domain.value_objects.id import ID
from auth_app.domain.value_objects.email import Email


class UserRepository(ABC):
    """Repository interface for User entities."""

    @abstractmethod
    def add(self, user: UserEntity) -> UserEntity:
        """Create a new user in the database."""
        pass

    @abstractmethod
    def save(self, user: UserEntity) -> UserEntity:
        """Update an existing user in the database."""
        pass

    @abstractmethod
    def delete(self, id: ID) -> None:
        """Delete a user by ID."""
        pass

    @abstractmethod
    def get_by_id(self, id: ID) -> UserEntity:
        """Get a user by ID."""
        pass

    @abstractmethod
    def get_by_email(self, email: Email) -> UserEntity:
        """Get a user by email."""
        pass

    @abstractmethod
    def exists_by_id(self, id: ID) -> bool:
        """Check if a user exists by ID."""
        pass

    @abstractmethod
    def exists_by_email(self, email: Email) -> bool:
        """Check if a user exists by email."""
        pass
