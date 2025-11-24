import logging
from django.contrib.auth.models import User
from .kafka_producer import publish_user_created

logger = logging.getLogger(__name__)


def signup_user(username: str, email: str, password: str) -> User:
    """
    Business logic for signing up a new user.

    Steps:
    1. Create the user in the database (password hashed by Django).
    2. Publish 'user_created' event to Kafka for other services.
    3. Log success or errors.
    """
    try:
        user = User.objects.create_user(
            username=username, email=email, password=password
        )
        logger.info(f"User created in DB: {user.id}, username: {username}")

        # Publish Kafka event
        publish_user_created(user.id, username, email)
        logger.info(f"Published user_created event for user_id={user.id}")

        return user
    except Exception as e:
        logger.error(f"Failed to create user {username}: {e}", exc_info=True)
        raise
