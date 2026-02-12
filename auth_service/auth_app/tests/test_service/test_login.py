import pytest
import fakeredis
from unittest.mock import MagicMock
from auth_app.service.login_service import LoginService
from auth_app.infrastructure.persistence.repositories.user_repository import (
    DjangoUserRepository,
)
from auth_app.infrastructure.cache.session_repository import RedisSessionRepository
from auth_app.infrastructure.messaging.event_publisher import EventPublisher
from auth_app.infrastructure.security.jwt_tools import JWT_Tools
from auth_app.infrastructure.security.password_hasher import PasswordHasher
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestLogin:
    fake_redis = fakeredis.FakeRedis()

    def test_login_success(self):
        user = User(username="TestUser556", email="testmail@test.com")
        user.set_password("TestPassword123666")
        user.save()

        producer = MagicMock()

        login_service = LoginService(
            user_repo=DjangoUserRepository(),
            session_repo=RedisSessionRepository(redis_client=self.fake_redis),
            event_publisher=EventPublisher(
                producer=producer, default_topic="test-topic"
            ),
            jwt_tools=JWT_Tools(),
            password_hasher=PasswordHasher(),
        )

        access_token, refresh_token = login_service.execute(
            username="TestUser556",
            email="testmail@test.com",
            password="TestPassword123666",
            device="test-device",
        )
