import pytest
import fakeredis
import jwt
from unittest.mock import patch, MagicMock
from django.urls import reverse
from rest_framework import status
from django.contrib.auth import get_user_model
from auth_app.infrastructure.security.jwt_tools import JWT_Tools
from datetime import datetime, timedelta, timezone
from django.conf import settings

User = get_user_model()


@pytest.mark.django_db
class TestE2E:
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
    def signup_url(self):
        return reverse("signup")
    
    @pytest.fixture
    def logout_url(self):
        return reverse("logout")
    
    @pytest.fixture
    def login_url(self):
        return reverse("login")
    
    @pytest.fixture
    def rotation_url(self):
        return reverse("rotation")
    
    @pytest.fixture
    def delac_url(self):
        return reverse("delac")

    @pytest.fixture
    def valid_user_data(self):
        return {
            "username": "testuser",
            "email": "testuser@example.com",
            "password": "StrongPassword123!",
        }

    def test_e2e_web(
            self, 
            client, 
            signup_url,
            logout_url,
            login_url,
            rotation_url,
            delac_url,
            valid_user_data
        ):
        ##### Sign Up #####
        signup_response = client.post(
            signup_url,
            valid_user_data,
            format="json",
            HTTP_USER_AGENT="pytest-agent",
        )

        assert signup_response.status_code == status.HTTP_200_OK
        assert signup_response.data["message"] == "User registered successfully."

        # --- User created ---
        user = User.objects.get(username=valid_user_data["username"])
        assert user.username == valid_user_data["username"]
        assert user.email == valid_user_data["email"]

        # --- Cookies set ---
        assert "access" in signup_response.cookies
        assert "refresh" in signup_response.cookies

        access_token = signup_response.cookies["access"].value
        refresh_token = signup_response.cookies["refresh"].value

        # --- Tokens valid ---
        access_payload = JWT_Tools.decode_token(access_token)
        refresh_payload = JWT_Tools.decode_token(refresh_token)

        assert access_payload["sub"] == str(user.public_id)
        assert access_payload["type"] == "access"
        assert access_payload["username"] == user.username

        assert refresh_payload["sub"] == str(user.public_id)
        assert refresh_payload["type"] == "refresh"
        assert refresh_payload["username"] == user.username

        ##### Logout #####
        client.cookies.load({"refresh": refresh_token})
        logout_response = client.post(
            logout_url,
            {},
            format="json",
            HTTP_USER_AGENT="pytest-agent",
        )

        assert logout_response.status_code == status.HTTP_200_OK
        assert logout_response.data["message"] == "User logged out successfully."

        # --- Cookies deleted ---
        assert (
            "access" not in logout_response.cookies or logout_response.cookies["access"].value == ""
        )
        assert (
            "refresh" not in logout_response.cookies or logout_response.cookies["refresh"].value == ""
        )

        ##### Login #####
        login_response = client.post(
            login_url,
            valid_user_data,
            format="json",
            HTTP_USER_AGENT="pytest-agent",
        )

        assert login_response.status_code == status.HTTP_200_OK
        assert login_response.data["message"] == "User logged in successfully."

        # --- Cookies set ---
        assert "access" in login_response.cookies
        assert "refresh" in login_response.cookies

        # --- Tokens valid ---
        access_token = login_response.cookies["access"].value
        refresh_token = login_response.cookies["refresh"].value

        assert isinstance(access_token, str) and isinstance(refresh_token, str)

        JWT_Tools.decode_token(access_token)
        JWT_Tools.decode_token(refresh_token)

        sid = JWT_Tools.decode_token(refresh_token)["sid"]

        ##### Rotation #####
        client.cookies.load({"refresh": refresh_token})
        rotation_response = client.post(
            rotation_url,
            {},
            format="json",
            HTTP_USER_AGENT="pytest-agent",
        )

        assert rotation_response.status_code == status.HTTP_200_OK
        assert rotation_response.data["message"] == "Rotation finished successfully."

        assert "access" in rotation_response.cookies

        access_token = rotation_response.cookies["access"].value

        access_payload = JWT_Tools.decode_token(access_token)

        assert access_payload["sub"] == str(user.public_id)
        assert access_payload["type"] == "access"
        assert access_payload["username"] == user.username


        ##### Rotation with new refresh token #####
        exp = datetime.now(timezone.utc) + timedelta(days=1)
        exp = exp.timestamp()
        should_rotate_refresh_token = jwt.encode(
            {
                "sid": str(sid),
                "sub": str(user.public_id),
                "username": user.username,
                "exp": exp,
                "type": "refresh",
            }, 
            settings.JWT_SECRET, 
            algorithm=settings.JWT_ALGORITHM
        )
        client.cookies.load({"refresh": should_rotate_refresh_token})
        rotation2response = client.post(
            rotation_url,
            {},
            format="json",
            HTTP_USER_AGENT="pytest-agent",
        )

        assert rotation2response.status_code == status.HTTP_200_OK
        assert rotation2response.data["message"] == "Rotation finished successfully."

        assert "access" in rotation2response.cookies
        assert "refresh" in rotation2response.cookies

        access_token = rotation2response.cookies["access"].value
        refresh_token = rotation2response.cookies["refresh"].value

        # --- Tokens valid ---
        access_payload = JWT_Tools.decode_token(access_token)
        refresh_payload = JWT_Tools.decode_token(refresh_token)

        assert access_payload["sub"] == str(user.public_id)
        assert access_payload["type"] == "access"
        assert access_payload["username"] == user.username

        assert refresh_payload["sub"] == str(user.public_id)
        assert refresh_payload["type"] == "refresh"
        assert refresh_payload["username"] == user.username

        sid = JWT_Tools.decode_token(refresh_token)["sid"]

        ##### Delete Account #####
        client.cookies.load({"refresh": refresh_token})
        delac_response = client.post(
            delac_url,
            {},
            format="json",
            HTTP_USER_AGENT="pytest-agent",
        )

        assert delac_response.status_code == status.HTTP_200_OK
        assert delac_response.data["message"] == "Account deleted out successfully."

        # --- Cookies deleted ---
        assert (
            "access" not in delac_response.cookies or delac_response.cookies["access"].value == ""
        )
        assert (
            "refresh" not in delac_response.cookies or delac_response.cookies["refresh"].value == ""
        )

        # --- User deleted ---
        assert not User.objects.filter(public_id=str(user.public_id)).exists()

        # --- Session deleted ---
        key_session = f"session:{sid}"
        assert not self.fake_redis_client.hgetall(key_session)

    def test_e2e_android(
            self, 
            client, 
            signup_url,
            logout_url,
            login_url,
            rotation_url,
            delac_url,
            valid_user_data
        ):
        ##### Sign Up #####
        signup_response = client.post(
            signup_url,
            valid_user_data,
            format="json",
            HTTP_USER_AGENT="pytest-agent",
            HTTP_X_CLIENT="android"
        )

        assert signup_response.status_code == status.HTTP_200_OK

        assert "access" in signup_response.data
        assert "refresh" in signup_response.data
        assert signup_response.data["message"] == "User registered successfully."

        # --- User created ---
        user = User.objects.get(username=valid_user_data["username"])
        assert user.username == valid_user_data["username"]
        assert user.email == valid_user_data["email"]

        # --- No cookies ---
        assert "access" not in signup_response.cookies
        assert "refresh" not in signup_response.cookies

        # --- Tokens valid ---
        access_token = signup_response.data["access"]
        refresh_token = signup_response.data["refresh"]
        access_payload = JWT_Tools.decode_token(access_token)
        refresh_payload = JWT_Tools.decode_token(refresh_token)

        assert access_payload["sub"] == str(user.public_id)
        assert access_payload["type"] == "access"
        assert access_payload["username"] == user.username

        assert refresh_payload["sub"] == str(user.public_id)
        assert refresh_payload["type"] == "refresh"
        assert refresh_payload["username"] == user.username

        ##### Logout #####
        logout_response = client.post(
            logout_url,
            {"refresh":refresh_token},
            format="json",
            HTTP_USER_AGENT="pytest-agent",
            HTTP_X_CLIENT="android"
        )

        assert logout_response.status_code == status.HTTP_200_OK

        assert "access" not in logout_response.data
        assert "refresh" not in logout_response.data
        assert logout_response.data["message"] == "User logged out successfully."

        # --- No cookies ---
        assert "access" not in logout_response.cookies
        assert "refresh" not in logout_response.cookies

        ##### Login #####
        login_response = client.post(
            login_url,
            valid_user_data,
            format="json",
            HTTP_USER_AGENT="pytest-agent",
            HTTP_X_CLIENT="android"
        )

        assert login_response.status_code == status.HTTP_200_OK
        assert "access" in login_response.data
        assert "refresh" in login_response.data
        assert login_response.data["message"] == "User logged in successfully."

        # --- No cookies ---
        assert "access" not in login_response.cookies
        assert "refresh" not in login_response.cookies

        # --- Tokens valid ---
        access_token = login_response.data["access"]
        refresh_token = login_response.data["refresh"]

        assert isinstance(access_token, str) and isinstance(refresh_token, str)

        JWT_Tools.decode_token(access_token)
        JWT_Tools.decode_token(refresh_token)

        sid = JWT_Tools.decode_token(refresh_token)["sid"]

        ##### Rotation #####
        rotation_response = client.post(
            rotation_url,
            {"refresh":refresh_token},
            format="json",
            HTTP_USER_AGENT="pytest-agent",
            HTTP_X_CLIENT="android"
        )

        assert rotation_response.status_code == status.HTTP_200_OK

        assert rotation_response.data["message"] == "Rotation finished successfully."

        assert "access" in rotation_response.data
        access_payload = JWT_Tools.decode_token(rotation_response.data["access"])

        assert access_payload["sub"] == str(user.public_id)
        assert access_payload["type"] == "access"
        assert access_payload["username"] == user.username


        ##### Rotation with new refresh token #####
        exp = datetime.now(timezone.utc) + timedelta(days=1)
        exp = exp.timestamp()
        should_rotate_refresh_token = jwt.encode(
            {
                "sid": str(sid),
                "sub": str(user.public_id),
                "username": user.username,
                "exp": exp,
                "type": "refresh",
            }, 
            settings.JWT_SECRET, 
            algorithm=settings.JWT_ALGORITHM
        )
        rotation2response = client.post(
            rotation_url,
            {"refresh":should_rotate_refresh_token},
            format="json",
            HTTP_USER_AGENT="pytest-agent",
            HTTP_X_CLIENT="android"
        )

        assert rotation2response.status_code == status.HTTP_200_OK

        assert "access" in rotation2response.data
        assert "refresh" in rotation2response.data
        access_payload = JWT_Tools.decode_token(rotation2response.data["access"])
        refresh_token = rotation2response.data["refresh"]
        refresh_payload = JWT_Tools.decode_token(rotation2response.data["refresh"])

        assert access_payload["sub"] == str(user.public_id)
        assert access_payload["type"] == "access"
        assert access_payload["username"] == user.username

        assert refresh_payload["sub"] == str(user.public_id)
        assert refresh_payload["type"] == "refresh"
        assert refresh_payload["username"] == user.username

        sid = JWT_Tools.decode_token(refresh_token)["sid"]

        ##### Delete Account #####
        delac_response = client.post(
            delac_url,
            {"refresh": refresh_token},
            format="json",
            HTTP_USER_AGENT="pytest-agent",
            HTTP_X_CLIENT="android"
        )

        assert delac_response.status_code == status.HTTP_200_OK

        assert "access" not in delac_response.data
        assert "refresh" not in delac_response.data
        assert delac_response.data["message"] == "Account deleted out successfully."

        # --- No cookies ---
        assert "access" not in delac_response.cookies
        assert "refresh" not in delac_response.cookies

        # --- User deleted ---
        assert not User.objects.filter(public_id=user.public_id).exists()

        # --- Session deleted ---
        key_session = f"session:{sid}"
        assert not self.fake_redis_client.hgetall(key_session)