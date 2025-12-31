from abc import ABC, abstractmethod
from domain.entities.user import UserEntity
from domain.value_objects.id import ID
from domain.value_objects.email import Email


class UserRepository(ABC):

    @abstractmethod
    def add(self, user: UserEntity) -> UserEntity:
        pass

    @abstractmethod
    def save(self, user: UserEntity) -> UserEntity:
        pass

    @abstractmethod
    def delete(self, id: ID) -> None:
        pass

    @abstractmethod
    def get_by_id(self, id: ID) -> UserEntity:
        pass

    @abstractmethod
    def get_by_email(self, email: Email) -> UserEntity:
        pass

    @abstractmethod
    def exists_by_id(self, id: ID) -> bool:
        pass

    @abstractmethod
    def exists_by_email(self, email: Email) -> bool:
        pass
