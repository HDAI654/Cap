import pytest
from core.exceptions import AuthenticationFailed
from unittest.mock import MagicMock
import jwt
import fakeredis
from django.conf import settings
from auth_app.infrastructure.persistence.repositories.user_repository import (
    DjangoUserRepository,
)
from auth_app.infrastructure.cache.session_repository import RedisSessionRepository
from auth_app.domain.factories.session_factory import SessionFactory
from auth_app.infrastructure.cache.session_repository import RedisSessionRepository
from auth_app.infrastructure.messaging.event_publisher import EventPublisher
from auth_app.infrastructure.security.jwt_tools import JWT_Tools
from auth_app.domain.factories.user_factory import UserFactory
from auth_app.service.del_account_service import DelAccountService
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta, timezone

User = get_user_model()


@pytest.mark.django_db
class TestDelAccount:
    fake_redis = fakeredis.FakeRedis()

    def test_del_account_success(self):
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

        exp = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

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

        producer = MagicMock()

        logout_service = DelAccountService(
            user_repo=user_repo,
            session_repo=session_repo,
            event_publisher=EventPublisher(
                producer=producer, default_topic="test-topic"
            ),
            jwt_tools=JWT_Tools(),
        )

        logout_service.execute(refresh_token=refresh_token)

    def test_del_account_with_invalid_token(self):
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

        exp = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        # create invalid tokens
        invalid_refresh_token = "invalid-refresh-token"
        incomplete_refresh_token = jwt.encode(
            {
                "sid": session.id.value, # remove 'sub'
                "username": user.username.value,
                "exp": exp,
                "type": "refresh",
            }, 
            settings.JWT_SECRET, 
            algorithm=settings.JWT_ALGORITHM
        )
        invalid_type_refresh_token = jwt.encode(
            {
                "sid": session.id.value,
                "sub": user.id.value,
                "username": user.username.value,
                "exp": exp,
                "type": "access",
            },
            settings.JWT_SECRET, 
            algorithm=settings.JWT_ALGORITHM
        )
        invalid_data_refresh_token = jwt.encode(
            {
                "sid": "شناسه اشتباه",
                "sub": user.id.value,
                "username": user.username.value,
                "exp": exp,
                "type": "refresh",
            },
            settings.JWT_SECRET, 
            algorithm=settings.JWT_ALGORITHM
        )
        invalid_data2_refresh_token = jwt.encode(
            {
                "sid": session.id.value,
                "sub": "شناسه اشتباه",
                "username": user.username.value,
                "exp": exp,
                "type": "refresh",
            },
            settings.JWT_SECRET, 
            algorithm=settings.JWT_ALGORITHM
        )
        expired_refresh_token =jwt.encode(
            {
                "sid": session.id.value,
                "sub": user.id.value,
                "username": user.username.value,
                "exp": datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS-1),
                "type": "refresh",
            },
            settings.JWT_SECRET, 
            algorithm=settings.JWT_ALGORITHM
        )
        nonexistent_user_refresh_token =jwt.encode(
            {
                "sid": session.id.value,
                "sub": "nonexistent",
                "username": user.username.value,
                "exp": exp,
                "type": "refresh",
            },
            settings.JWT_SECRET, 
            algorithm=settings.JWT_ALGORITHM
        )
        nonexistent_session_refresh_token =jwt.encode(
            {
                "sid": "nonexistent",
                "sub": user.id.value,
                "username": user.username.value,
                "exp": exp,
                "type": "refresh",
            },
            settings.JWT_SECRET, 
            algorithm=settings.JWT_ALGORITHM
        )


        producer = MagicMock()

        logout_service = DelAccountService(
            user_repo=user_repo,
            session_repo=session_repo,
            event_publisher=EventPublisher(
                producer=producer, default_topic="test-topic"
            ),
            jwt_tools=JWT_Tools(),
        )

        with pytest.raises(AuthenticationFailed):
            logout_service.execute(
                refresh_token=invalid_refresh_token
            )
            logout_service.execute(
                refresh_token=incomplete_refresh_token
            )
            logout_service.execute(
                refresh_token=invalid_type_refresh_token
            )
            logout_service.execute(
                refresh_token=invalid_data_refresh_token
            )
            logout_service.execute(
                refresh_token=invalid_data2_refresh_token
            )
            logout_service.execute(
                refresh_token=expired_refresh_token
            )
            logout_service.execute(
                refresh_token=nonexistent_user_refresh_token
            )
            logout_service.execute(
                refresh_token=nonexistent_session_refresh_token
            )


