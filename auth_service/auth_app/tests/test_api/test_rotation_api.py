import pytest
import fakeredis
from unittest.mock import patch, MagicMock
from django.urls import reverse
from rest_framework import status
from django.contrib.auth import get_user_model
from auth_app.infrastructure.security.jwt_tools import JWT_Tools
from auth_app.infrastructure.security.password_hasher import PasswordHasher
from auth_app.domain.factories.user_factory import UserFactory
from auth_app.domain.factories.session_factory import SessionFactory
import jwt
from datetime import datetime, timedelta, timezone
from django.conf import settings

User = get_user_model()


@pytest.mark.django_db
class TestRotationEndpoint:
    @pytest.fixture(scope="class")
    def fake_redis(self):
        return fakeredis.FakeStrictRedis()

    @pytest.fixture(autouse=True)
    def setup(self, mocker, fake_redis):
        self.fake_redis_client = fake_redis
        self.fake_kafka_producer = MagicMock()

        mocker.patch(
            "auth_app.infrastructure.cache.redis_client.get_redis_client",
            return_value=self.fake_redis_client,
        )
        mocker.patch(
            "auth_app.infrastructure.messaging.kafka_producer.get_producer",
            return_value=self.fake_kafka_producer,
        )

    @pytest.fixture
    def rotation_url(self):
        return reverse("rotation")

    @pytest.fixture
    def test_user(self):
        user = UserFactory.create(
            username="testuser",
            email="testuser@example.com",
            hashed_password=PasswordHasher().hash("StrongPassword123!"),
        )
        _user = User(
            public_id=user.id.value,
            username="testuser",
            email="testuser@example.com",
        )
        _user.set_password("StrongPassword123!")
        _user.save()
        return user

    @pytest.fixture
    def test_session(self, test_user):
        session = SessionFactory.create(
            user_id=test_user.id.value,
        )
        key_session = f"session:{session.id.value}"
        key_user_sessions = f"user:{session.user_id.value}"
        self.fake_redis_client.hset(
            key_session,
            mapping={
                "user_id": session.user_id.value,
                "device": session.device.value,
                "created_at": session.created_at.value,
            },
        )

        self.fake_redis_client.sadd(key_user_sessions, session.id.value)

        return session

    @pytest.fixture
    def valid_payload(self, test_user, test_session):
        return {
            "refresh": JWT_Tools.create_refresh_token(
                user_id=test_user.id,
                username=test_user.username,
                session_id=test_session.id,
            ),
        }
    
    @pytest.fixture
    def valid_should_rotate_payload(self, test_user, test_session):
        exp = datetime.now(timezone.utc) + timedelta(
            days=1
        )
        exp = exp.timestamp()
        payload = {
            "sid": test_session.id.value,
            "sub": test_user.id.value,
            "username": test_user.username.value,
            "exp": exp,
            "type": "refresh",
        }
        refresh_token = jwt.encode(
            payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
        )
        return {
            "refresh": refresh_token,
        }

    def test_rotation_success_web(
        self, client, mocker, rotation_url, valid_payload, test_user, test_session
    ):
        mock_get_by_id = mocker.patch(
            "auth_app.infrastructure.cache.session_repository.RedisSessionRepository.get_by_id"
        )
        mock_get_by_id.return_value = test_session

        client.cookies.load({"refresh": valid_payload["refresh"]})
        response = client.post(
            rotation_url,
            {},
            format="json",
            HTTP_USER_AGENT="pytest-agent",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["message"] == "Rotation finished successfully."

        assert "access" in response.cookies

        access_token = response.cookies["access"].value

        access_payload = JWT_Tools.decode_token(access_token)

        assert access_payload["sub"] == str(test_user.id)
        assert access_payload["type"] == "access"
        assert access_payload["username"] == test_user.username

    def test_rotation_success_android(
        self, client, mocker, rotation_url, valid_payload, test_user, test_session
    ):
        mock_get_by_id = mocker.patch(
            "auth_app.infrastructure.cache.session_repository.RedisSessionRepository.get_by_id"
        )
        mock_get_by_id.return_value = test_session

        response = client.post(
            rotation_url,
            valid_payload,
            format="json",
            HTTP_USER_AGENT="pytest-agent",
            HTTP_X_CLIENT="android",
        )

        assert response.status_code == status.HTTP_200_OK

        assert response.data["message"] == "Rotation finished successfully."

        assert "access" in response.data
        access_payload = JWT_Tools.decode_token(response.data["access"])

        assert access_payload["sub"] == str(test_user.id)
        assert access_payload["type"] == "access"
        assert access_payload["username"] == test_user.username

    def test_rotation_success_web_with_new_refresh_token(
        self, client, mocker, rotation_url, valid_should_rotate_payload, test_user, test_session
    ):
        mock_get_by_id = mocker.patch(
            "auth_app.infrastructure.cache.session_repository.RedisSessionRepository.get_by_id"
        )
        mock_get_by_id.return_value = test_session

        client.cookies.load({"refresh": valid_should_rotate_payload["refresh"]})
        response = client.post(
            rotation_url,
            {},
            format="json",
            HTTP_USER_AGENT="pytest-agent",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["message"] == "Rotation finished successfully."

        assert "access" in response.cookies
        assert "refresh" in response.cookies

        access_token = response.cookies["access"].value
        refresh_token = response.cookies["refresh"].value

        # --- Tokens valid ---
        access_payload = JWT_Tools.decode_token(access_token)
        refresh_payload = JWT_Tools.decode_token(refresh_token)

        assert access_payload["sub"] == str(test_user.id)
        assert access_payload["type"] == "access"
        assert access_payload["username"] == test_user.username

        assert refresh_payload["sub"] == str(test_user.id)
        assert refresh_payload["type"] == "refresh"
        assert refresh_payload["username"] == test_user.username

    def test_rotation_success_android_with_new_refresh_token(
        self, client, mocker, rotation_url, valid_should_rotate_payload, test_user, test_session
    ):
        mock_get_by_id = mocker.patch(
            "auth_app.infrastructure.cache.session_repository.RedisSessionRepository.get_by_id"
        )
        mock_get_by_id.return_value = test_session

        response = client.post(
            rotation_url,
            valid_should_rotate_payload,
            format="json",
            HTTP_USER_AGENT="pytest-agent",
            HTTP_X_CLIENT="android",
        )

        assert response.status_code == status.HTTP_200_OK

        assert "access" in response.data
        assert "refresh" in response.data
        access_payload = JWT_Tools.decode_token(response.data["access"])
        refresh_payload = JWT_Tools.decode_token(response.data["refresh"])

        assert access_payload["sub"] == str(test_user.id)
        assert access_payload["type"] == "access"
        assert access_payload["username"] == test_user.username

        assert refresh_payload["sub"] == str(test_user.id)
        assert refresh_payload["type"] == "refresh"
        assert refresh_payload["username"] == test_user.username
