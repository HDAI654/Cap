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

User = get_user_model()


@pytest.mark.django_db
class TestDelAccountEndpoint:
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
    def delac_url(self):
        return reverse("delac")

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
    def access_token(self, test_user):
        return JWT_Tools.create_access_token(
            user_id=test_user.id,
            username=test_user.username,
        )

    def test_delac_success_web(
        self,
        client,
        mocker,
        delac_url,
        valid_payload,
        test_user,
        test_session,
        access_token,
    ):
        mock_get_by_id = mocker.patch(
            "auth_app.infrastructure.cache.session_repository.RedisSessionRepository.get_by_id"
        )
        mock_get_by_id.return_value = test_session

        client.cookies.load(
            {"refresh": valid_payload["refresh"], "access": access_token}
        )
        response = client.post(
            delac_url,
            {},
            format="json",
            HTTP_USER_AGENT="pytest-agent",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["message"] == "Account deleted out successfully."

        # --- Cookies deleted ---
        assert (
            "access" not in response.cookies or response.cookies["access"].value == ""
        )
        assert (
            "refresh" not in response.cookies or response.cookies["refresh"].value == ""
        )

        # --- User deleted ---
        assert not User.objects.filter(public_id=test_user.id.value).exists()

        # --- Session deleted ---
        key_session = f"session:{test_session.id.value}"
        assert not self.fake_redis_client.hgetall(key_session)

    def test_delac_success_android(
        self,
        client,
        mocker,
        delac_url,
        valid_payload,
        test_user,
        test_session,
        access_token,
    ):
        mock_get_by_id = mocker.patch(
            "auth_app.infrastructure.cache.session_repository.RedisSessionRepository.get_by_id"
        )
        mock_get_by_id.return_value = test_session

        response = client.post(
            delac_url,
            valid_payload,
            format="json",
            HTTP_USER_AGENT="pytest-agent",
            HTTP_X_CLIENT="android",
            HTTP_AUTHORIZATION=f"Bearer {access_token}",
        )

        assert response.status_code == status.HTTP_200_OK

        assert "access" not in response.data
        assert "refresh" not in response.data
        assert response.data["message"] == "Account deleted out successfully."

        # --- No cookies ---
        assert "access" not in response.cookies
        assert "refresh" not in response.cookies

        # --- User deleted ---
        assert not User.objects.filter(public_id=test_user.id.value).exists()

        # --- Session deleted ---
        key_session = f"session:{test_session.id.value}"
        assert not self.fake_redis_client.hgetall(key_session)

    def test_block_request_without_access_token(
        self,
        client,
        mocker,
        delac_url,
        valid_payload,
        test_user,
        test_session,
        access_token,
    ):
        mock_get_by_id = mocker.patch(
            "auth_app.infrastructure.cache.session_repository.RedisSessionRepository.get_by_id"
        )
        mock_get_by_id.return_value = test_session

        # ANDROID/IOS
        response = client.post(
            delac_url,
            valid_payload,
            format="json",
            HTTP_USER_AGENT="pytest-agent",
            HTTP_X_CLIENT="android",
            HTTP_AUTHORIZATION=f"{access_token}",  # incorrect token
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

        response = client.post(
            delac_url,
            valid_payload,
            format="json",
            HTTP_USER_AGENT="pytest-agent",
            HTTP_X_CLIENT="android",
            HTTP_AUTHORIZATION=f"{access_token}",  # missed token
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

        # Web
        response = client.post(
            delac_url,
            valid_payload,
            format="json",
            HTTP_USER_AGENT="pytest-agent",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
