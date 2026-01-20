import pytest
import unittest
import jwt
import fakeredis
from datetime import datetime, timedelta, timezone
from django.conf import settings
from unittest.mock import patch
from auth_app.infrastructure.persistence.repositories.user_repository import (
    DjangoUserRepository,
)
from auth_app.infrastructure.cache.session_repository import RedisSessionRepository
from auth_app.domain.factories.session_factory import SessionFactory
from auth_app.infrastructure.security.jwt_tools import JWT_Tools
from auth_app.domain.factories.user_factory import UserFactory
from auth_app.service.token_rotation_service import TokenRotationService
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestRotation:
    fake_redis = fakeredis.FakeRedis()

    @pytest.fixture()
    def user(self):
        return UserFactory.create(
            username="TestUser556",
            email="testmail@test.com",
            hashed_password="HashedTestPassword12354",
        )

    def test_rotation_success(self, user):
        user_repo = DjangoUserRepository()
        user_repo.add(user)

        session_repo = RedisSessionRepository(redis_client=self.fake_redis)

        exp = datetime.now(timezone.utc) + timedelta(days=30)

        session = SessionFactory.create(user_id=user.id.value, device="test-device")
        session_repo.add(session)

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

        rotation_service = TokenRotationService(
            user_repo=user_repo, session_repo=session_repo, jwt_tools=JWT_Tools()
        )

        new_access, new_refresh = rotation_service.execute(
            refresh_token=refresh_token, device="test-device"
        )
        assert new_access
        assert new_refresh is None
        assert isinstance(new_access, str)

    def test_rotation_success_with_new_refresh_token(self, user):
        user_repo = DjangoUserRepository()
        user_repo.add(user)

        session_repo = RedisSessionRepository(redis_client=self.fake_redis)

        exp = datetime.now(timezone.utc) + timedelta(minutes=1)

        session = SessionFactory.create(user_id=user.id.value, device="test-device")
        session_repo.add(session)

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

        rotation_service = TokenRotationService(
            user_repo=user_repo, session_repo=session_repo, jwt_tools=JWT_Tools()
        )

        new_access, new_refresh = rotation_service.execute(
            refresh_token=refresh_token, device="test-device"
        )
        assert new_access and new_refresh
        assert isinstance(new_access, str) and isinstance(new_refresh, str)
