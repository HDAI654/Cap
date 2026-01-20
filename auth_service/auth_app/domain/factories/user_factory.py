from auth_app.domain.entities.user import UserEntity
from auth_app.domain.value_objects.id import ID
from auth_app.domain.value_objects.username import Username
from auth_app.domain.value_objects.email import Email
from auth_app.domain.value_objects.password import Password


class UserFactory:
    @staticmethod
    def create(
        *,
        username: str,
        email: str,
        hashed_password: str,
        user_id: str | None = None,
    ) -> UserEntity:
        """
        Create a new UserEntity.
        """

        return UserEntity(
            id=ID(user_id),
            username=Username(username),
            email=Email(email),
            password=Password(hashed_password),
        )
