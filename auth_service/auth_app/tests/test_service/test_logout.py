import pytest
import jwt
import fakeredis
from django.conf import settings
from auth_app.infrastructure.persistence.repositories.user_repository import (
    DjangoUserRepository,
)
from auth_app.infrastructure.cache.session_repository import RedisSessionRepository
from auth_app.domain.factories.session_factory import SessionFactory
from auth_app.infrastructure.security.jwt_tools import JWT_Tools
from auth_app.domain.factories.user_factory import UserFactory
from auth_app.service.logout_service import LogoutService
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta, timezone

User = get_user_model()


@pytest.mark.django_db
class TestRotation:
    fake_redis = fakeredis.FakeRedis()

    def test_rotation_success(self):
        user = UserFactory.create(
            username="TestUser",
            email="Test@test.com",
            hashed_password="test-password1558",
        )

        user_repo = DjangoUserRepository()
        user_repo.add(user)

        session_repo = RedisSessionRepository(redis_client=self.fake_redis)

        session = SessionFactory.create(user_id=user.id.value, device="test-device")
        session_repo.add(session)

        exp = datetime.now(timezone.utc) + timedelta(days=30)

        payload = {
            "sid": session.id.value,
            "sub": user.id.value,
            "username": user.username.value,
            "exp": exp,
            "type": "refresh",
        }
        refresh_token = jwt.encode(
            payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
        )

        logout_service = LogoutService(
            user_repo=user_repo, session_repo=session_repo, jwt_tools=JWT_Tools()
        )

        logout_service.execute(refresh_token=refresh_token)
