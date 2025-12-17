import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from accounts.services.jwt_service import JWT_Tools
from accounts.services.session_service import SessionManager
from unittest.mock import Mock
import jwt
from django.conf import settings

User = get_user_model()


@pytest.fixture
def refresh_url():
    return reverse("token_refresh")


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="testuser", email="test@example.com", password="password123"
    )


@pytest.fixture
def session(user):
    sess = SessionManager.new_session(user_id=user.id, device="pytest-agent")
    sess.save()
    return sess


@pytest.mark.django_db
def test_refresh_success_web(client, user, session, mocker, refresh_url):
    # Mock decode_token to return payload
    payload = {"sub": user.id, "sid": session.id, "type": "refresh"}
    mocker.patch.object(JWT_Tools, "decode_token", return_value=payload)
    mocker.patch.object(
        JWT_Tools, "create_access_token", return_value="new-access-token"
    )

    # Set refresh token in cookie
    client.cookies["refresh"] = "mock-refresh-token"

    response = client.post(refresh_url, {}, format="json", HTTP_USER_AGENT="web")

    assert response.status_code == status.HTTP_200_OK
    assert response.cookies["access"].value == "new-access-token"
    assert response.data["message"] == "Token refreshed"


@pytest.mark.django_db
def test_refresh_success_android(client, user, session, mocker, refresh_url):
    payload = {"sub": user.id, "sid": session.id, "type": "refresh"}
    mocker.patch.object(JWT_Tools, "decode_token", return_value=payload)
    mocker.patch.object(
        JWT_Tools, "create_access_token", return_value="new-access-token"
    )

    response = client.post(
        refresh_url,
        {"refresh": "mock-refresh-token"},
        format="json",
        HTTP_X_CLIENT="android",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["access"] == "new-access-token"


@pytest.mark.django_db
def test_refresh_missing_token(client, refresh_url):
    response = client.post(refresh_url, {}, format="json")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data["error"] == "Refresh token missing"


@pytest.mark.django_db
def test_refresh_invalid_token(client, mocker, refresh_url):
    mocker.patch.object(JWT_Tools, "decode_token", side_effect=Exception("invalid"))
    response = client.post(
        refresh_url, {"refresh": "bad-token"}, format="json", HTTP_X_CLIENT="android"
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data["error"] == "Invalid token"


@pytest.mark.django_db
def test_refresh_expired_token(client, mocker, refresh_url):
    mocker.patch.object(
        JWT_Tools, "decode_token", side_effect=jwt.ExpiredSignatureError
    )
    response = client.post(
        refresh_url,
        {"refresh": "expired-token"},
        format="json",
        HTTP_X_CLIENT="android",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data["error"] == "Refresh token expired"


@pytest.mark.django_db
def test_refresh_invalid_user(client, session, mocker, refresh_url):
    payload = {"sub": 99999, "sid": session.id, "type": "refresh"}  # Non-existent user
    mocker.patch.object(JWT_Tools, "decode_token", return_value=payload)

    response = client.post(
        refresh_url, {"refresh": "token"}, format="json", HTTP_X_CLIENT="android"
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data["error"] == "Invalid credentials"


@pytest.mark.django_db
def test_refresh_invalid_session(client, user, mocker, refresh_url):
    payload = {"sub": user.id, "sid": "invalid-session", "type": "refresh"}
    mocker.patch.object(JWT_Tools, "decode_token", return_value=payload)

    response = client.post(
        refresh_url, {"refresh": "token"}, format="json", HTTP_X_CLIENT="android"
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data["error"] == "Invalid credentials"
