import logging
from django.contrib.auth import get_user_model
from django.db.models import Q

from auth_app.domain.entities.user import UserEntity
from auth_app.domain.factories.user_factory import UserFactory
from auth_app.domain.repositories.user_repository import UserRepository
from auth_app.domain.value_objects.id import ID
from auth_app.domain.value_objects.email import Email
from auth_app.domain.value_objects.username import Username
from auth_app.domain.value_objects.password import Password
from core.exceptions import UserAlreadyExists, UserNotFound

User = get_user_model()
logger = logging.getLogger(__name__)


class DjangoUserRepository(UserRepository):

    def add(self, user: UserEntity) -> UserEntity:
        """
        Add a NEW user to DB.
        """
        if self.exists_by_email(user.email):
            raise UserAlreadyExists("Email already exists")

        if User.objects.filter(username=user.username.value).exists():
            raise UserAlreadyExists("Username already exists")

        django_user = User.objects.create(
            public_id=user.id.value,
            username=user.username.value,
            email=user.email.value,
            password=user.password.value,
        )
        logger.info(
            "User created: public_id=%s username=%s",
            user.id.value,
            user.username.value,
        )
        return self._to_entity(django_user)

    def save(self, user: UserEntity) -> UserEntity:
        """
        Update an EXISTING user.
        """
        try:
            django_user = User.objects.get(public_id=user.id.value)
        except User.DoesNotExist:
            raise UserNotFound(f"User with ID '{user.id.value}' not found")

        if User.objects.filter(
            Q(email=user.email.value) & ~Q(public_id=user.id.value)
        ).exists():
            raise UserAlreadyExists("This email is being used by another user!")

        if User.objects.filter(
            Q(username=user.username.value) & ~Q(public_id=user.id.value)
        ).exists():
            raise UserAlreadyExists("This username is being used by another user!")

        django_user.username = user.username.value
        django_user.email = user.email.value
        django_user.password = user.password.value
        django_user.save()

        logger.info(
            "User updated: public_id=%s username=%s",
            user.id.value,
            user.username.value,
        )

        return self._to_entity(django_user)

    def delete(self, id: ID) -> None:
        try:
            django_user = User.objects.get(public_id=id.value)
        except User.DoesNotExist:
            raise UserNotFound(f"User with ID '{id.value}' not found")
        django_user.delete()
        logger.info("User deleted: public_id=%s", id.value)

    def get_by_id(self, id: ID) -> UserEntity:
        try:
            django_user = User.objects.get(public_id=id.value)
            return self._to_entity(django_user)
        except User.DoesNotExist:
            raise UserNotFound(f"User with ID '{id.value}' not found")

    def get_by_email(self, email: Email) -> UserEntity:
        try:
            django_user = User.objects.get(email=email.value)
            return self._to_entity(django_user)
        except User.DoesNotExist:
            raise UserNotFound(f"User with email '{email.value}' not found")

    def exists_by_id(self, id: ID) -> bool:
        return User.objects.filter(public_id=id.value).exists()

    def exists_by_email(self, email: Email) -> bool:
        return User.objects.filter(email=email.value).exists()

    def _to_entity(self, django_user) -> UserEntity:
        """
        Map Django model → Domain Entity
        """
        return UserFactory.create(
            user_id=str(django_user.public_id),
            username=str(django_user.username),
            email=str(django_user.email),
            hashed_password=str(django_user.password),
        )
