import pytest
import fakeredis
from unittest.mock import patch, MagicMock
from django.urls import reverse
from rest_framework import status
from django.contrib.auth import get_user_model
from auth_app.infrastructure.security.jwt_tools import JWT_Tools

User = get_user_model()


@pytest.mark.django_db
class TestLoginEndpoint:

    @pytest.fixture(autouse=True)
    def setup(self, mocker):
        self.fake_redis_client = fakeredis.FakeStrictRedis()
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
    def test_user(self):
        user = User(
            username="testuser",
            email="testuser@example.com",
        )
        user.set_password("StrongPassword123!")
        user.save()
        return user

    @pytest.fixture
    def login_url(self):
        return reverse("login")

    @pytest.fixture
    def valid_payload(self, test_user):
        return {
            "username": "testuser",
            "email": "testuser@example.com",
            "password": "StrongPassword123!",
        }

    def test_login_success_web(self, client, mocker, login_url, valid_payload):
        response = client.post(
            login_url,
            valid_payload,
            format="json",
            HTTP_USER_AGENT="pytest-agent",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["message"] == "User logged in successfully."

        # --- Cookies set ---
        assert "access" in response.cookies
        assert "refresh" in response.cookies

        # --- Tokens valid ---
        access_token = response.cookies["access"].value
        refresh_token = response.cookies["refresh"].value

        assert isinstance(access_token, str) and isinstance(refresh_token, str)

        JWT_Tools.decode_token(access_token)
        JWT_Tools.decode_token(refresh_token)

    def test_login_success_android(self, client, mocker, login_url, valid_payload):
        response = client.post(
            login_url,
            valid_payload,
            format="json",
            HTTP_USER_AGENT="pytest-agent",
            HTTP_X_CLIENT="android",
        )

        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data
        assert response.data["message"] == "User logged in successfully."

        # --- No cookies ---
        assert "access" not in response.cookies
        assert "refresh" not in response.cookies

        # --- Tokens valid ---
        access_token = response.data["access"]
        refresh_token = response.data["refresh"]

        assert isinstance(access_token, str) and isinstance(refresh_token, str)

        JWT_Tools.decode_token(access_token)
        JWT_Tools.decode_token(refresh_token)
