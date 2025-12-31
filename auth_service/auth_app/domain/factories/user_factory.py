from domain.entities.user import UserEntity
from domain.value_objects.id import ID
from domain.value_objects.username import Username
from domain.value_objects.email import Email
from domain.value_objects.password import Password


class UserFactory:
    @staticmethod
    def create(
        *,
        username: str,
        email: str,
        hashed_password: str,
        user_id: ID | None = None,
    ) -> UserEntity:
        """
        Create a new UserEntity.
        """

        return UserEntity(
            id=user_id or ID(),
            username=Username(username),
            email=Email(email),
            password=Password(hashed_password),
        )
