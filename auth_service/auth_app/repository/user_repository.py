import logging
from django.contrib.auth import get_user_model
from ..domain.user import UserEntity

User = get_user_model()

logger = logging.getLogger(__name__)

class UserRepo:
    @staticmethod
    def create_user(user: UserEntity) -> UserEntity:
        user_model = User(
            username=user.username, email=user.email
        )
        user_model.set_password(user.password)
        user_model.save()
        user.id = user_model.id
        logger.info(f"User created in DB: {user.id}, username: {user.username}")

        return user
