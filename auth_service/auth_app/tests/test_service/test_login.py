import pytest
import fakeredis
from unittest.mock import MagicMock
from auth_app.service.login_service import LoginService
from auth_app.infrastructure.persistence.repositories.user_repository import (
    DjangoUserRepository,
)
from core.exceptions import AuthenticationFailed, BadRequestError
from auth_app.infrastructure.cache.session_repository import RedisSessionRepository
from auth_app.infrastructure.messaging.event_publisher import EventPublisher
from auth_app.infrastructure.security.jwt_tools import JWT_Tools
from auth_app.infrastructure.security.password_hasher import PasswordHasher
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestLogin:
    fake_redis = fakeredis.FakeRedis()
    producer = MagicMock()

    login_service = LoginService(
        user_repo=DjangoUserRepository(),
        session_repo=RedisSessionRepository(redis_client=fake_redis),
        event_publisher=EventPublisher(
            producer=producer, default_topic="test-topic"
        ),
        jwt_tools=JWT_Tools(),
        password_hasher=PasswordHasher(),
    )

    def test_login_success(self):
        user = User(username="TestUser556", email="testmail@test.com")
        user.set_password("TestPassword123666")
        user.save()

        

        access_token, refresh_token = self.login_service.execute(
            username="TestUser556",
            email="testmail@test.com",
            password="TestPassword123666",
            device="test-device",
        )
        assert isinstance(access_token, str) and isinstance(refresh_token, str)

    def test_login_with_invalid_credentials(self):
        user = User(username="TestUser556", email="testmail@test.com")
        user.set_password("TestPassword123666")
        user.save()

        with pytest.raises(AuthenticationFailed):
            # nonexistent email
            self.login_service.execute(username="TestUser556", email="nonexistent.email@test.com", password="TestPassword123666", device="AndroidPhone")

            # incorrect password
            self.login_service.execute(
                username="TestUser556", 
                email="testmail@test.com", 
                password="invalid-password", 
                device="AndroidPhone"
            )

            # incorrect username
            self.login_service.execute(
                username="invalid-username", 
                email="testmail@test.com", 
                password="TestPassword123666", 
                device="AndroidPhone"
            )
    
    def test_login_with_invalid_email(self):
        with pytest.raises(BadRequestError):
            self.login_service.execute(
                username="invalid-username", 
                email="ایمیل اشتباه@test.com", 
                password="TestPassword123666", 
                device="AndroidPhone"
            )
            


