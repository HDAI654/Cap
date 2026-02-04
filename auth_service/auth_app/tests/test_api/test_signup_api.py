import pytest
import fakeredis
from unittest.mock import patch, MagicMock, call
from django.urls import reverse
from rest_framework import status
from django.contrib.auth import get_user_model
from auth_app.infrastructure.security.jwt_tools import JWT_Tools

User = get_user_model()


@pytest.mark.django_db
class TestSignupEndpoint:
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
    def signup_url(self):
        return reverse("signup")

    @pytest.fixture
    def valid_payload(self):
        return {
            "username": "testuser",
            "email": "testuser@example.com",
            "password": "StrongPassword123!",
        }

    def test_signup_success_web(self, client, mocker, signup_url, valid_payload):
        """
        WEB client:
        - user created
        - cookies set
        - no tokens in JSON body
        """

        response = client.post(
            signup_url,
            valid_payload,
            format="json",
            HTTP_USER_AGENT="pytest-agent",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data == {"message": "User registered successfully."}

        # --- User created ---
        user = User.objects.get(username=valid_payload["username"])
        assert user.username == valid_payload["username"]
        assert user.email == valid_payload["email"]

        # --- Cookies set ---
        assert "access" in response.cookies
        assert "refresh" in response.cookies

        access_token = response.cookies["access"].value
        refresh_token = response.cookies["refresh"].value

        # --- Tokens valid ---
        access_payload = JWT_Tools.decode_token(access_token)
        refresh_payload = JWT_Tools.decode_token(refresh_token)

        assert access_payload["sub"] == str(user.public_id)
        assert access_payload["type"] == "access"
        assert access_payload["username"] == user.username

        assert refresh_payload["sub"] == str(user.public_id)
        assert refresh_payload["type"] == "refresh"
        assert refresh_payload["username"] == user.username

    def test_signup_success_android(self, client, mocker, signup_url, valid_payload):
        """
        ANDROID client:
        - user created
        - no cookies
        - tokens returned in JSON
        """

        response = client.post(
            signup_url,
            valid_payload,
            format="json",
            HTTP_USER_AGENT="pytest-agent",
            HTTP_X_CLIENT="android",
        )

        assert response.status_code == status.HTTP_200_OK

        assert "access" in response.data
        assert "refresh" in response.data
        assert response.data["message"] == "User registered successfully."

        # --- User created ---
        user = User.objects.get(username=valid_payload["username"])
        assert user.username == valid_payload["username"]
        assert user.email == valid_payload["email"]

        # --- No cookies ---
        assert "access" not in response.cookies
        assert "refresh" not in response.cookies

        # --- Tokens valid ---
        access_payload = JWT_Tools.decode_token(response.data["access"])
        refresh_payload = JWT_Tools.decode_token(response.data["refresh"])

        assert access_payload["sub"] == str(user.public_id)
        assert access_payload["type"] == "access"
        assert access_payload["username"] == user.username

        assert refresh_payload["sub"] == str(user.public_id)
        assert refresh_payload["type"] == "refresh"
        assert refresh_payload["username"] == user.username
