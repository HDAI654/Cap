import logging
from django.contrib.auth import get_user_model
from ..domain.user import UserEntity
from django.contrib.auth import authenticate
from ...core.exceptions import AuthenticationFailed, UserAlreadyExists

User = get_user_model()

logger = logging.getLogger(__name__)


class UserRepo:
    @staticmethod
    def create_user(user: UserEntity) -> UserEntity:
        # Check for existing username
        if User.objects.filter(username=user.username).exists():
            raise UserAlreadyExists(f"Username '{user.username}' is already taken.")

        # Check for existing email if email is required
        if user.email and User.objects.filter(email=user.email).exists():
            raise UserAlreadyExists(f"Email '{user.email}' is already registered.")

        user_model = User(username=user.username, email=user.email)
        user_model.set_password(user.password)
        user_model.save()
        user.id = user_model.id
        logger.info(f"User created in DB: {user.id}, username: {user.username}")

        return user

    @staticmethod
    def authenticate(user: UserEntity) -> UserEntity:
        user_model = authenticate(username=user.username, password=user.password)
        if not user_model:
            raise AuthenticationFailed("Invalid username or password")

        user.id = user_model.id
        user.email = user_model.email

        return user

    def get_by_id(id: str) -> UserEntity:
        user_model = User.objects.get(id=id)
        return UserEntity.from_model(user_model)
