import pytest
import fakeredis
from unittest.mock import MagicMock, patch
from auth_app.service.signup_service import SignupService
from auth_app.infrastructure.persistence.repositories.user_repository import (
    DjangoUserRepository,
)
from core.exceptions import BadRequestError
from auth_app.infrastructure.cache.session_repository import RedisSessionRepository
from auth_app.infrastructure.messaging.event_publisher import EventPublisher
from auth_app.infrastructure.security.jwt_tools import JWT_Tools
from auth_app.infrastructure.security.password_hasher import PasswordHasher


@pytest.mark.django_db
class TestSignup:
    fake_redis = fakeredis.FakeRedis()

    producer = MagicMock()
    signup_service = SignupService(
        user_repo=DjangoUserRepository(),
        session_repo=RedisSessionRepository(redis_client=fake_redis),
        event_publisher=EventPublisher(producer=producer, default_topic="test-topic"),
        jwt_tools=JWT_Tools(),
        password_hasher=PasswordHasher(),
    )

    def test_signup_success(self):
        access_token, refresh_token = self.signup_service.execute(
            username="TestUser556",
            email="testmail@test.com",
            password="TestPassword123666",
            device="test-device",
        )

        assert isinstance(access_token, str) and isinstance(refresh_token, str)

    def test_signup_with_duplicate_username_or_email(self):
        self.signup_service.execute(
            username="TestUser556",
            email="testmail@test.com",
            password="TestPassword123666",
            device="test-device",
        )

        with pytest.raises(BadRequestError):
            self.signup_service.execute(
                username="DifferentUsername",
                email="testmail@test.com",
                password="TestPassword123666",
                device="test-device",
            )
            self.signup_service.execute(
                username="TestUser556",
                email="differentmail@test.com",
                password="TestPassword123666",
                device="test-device",
            )

    def test_signup_with_invalid_username_or_email(self):
        with pytest.raises(BadRequestError):
            self.signup_service.execute(
                username="نام کاربری",
                email="testmail@test.com",
                password="TestPassword123666",
                device="test-device",
            )
            self.signup_service.execute(
                username="TestUser556",
                email="ایمیل@test.com",
                password="TestPassword123666",
                device="test-device",
            )
