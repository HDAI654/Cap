import pytest
import jwt
from datetime import datetime, timedelta, timezone
from django.urls import reverse
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import status

from accounts.services.jwt_service import JWT_Tools
from accounts.services.session_service import SessionManager

User = get_user_model()


@pytest.fixture
def refresh_url():
    return reverse("token_refresh")


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="testuser",
        password="StrongPassword123!",
        email="testuser@example.com",
    )


@pytest.fixture
def session(user):
    return SessionManager.new_session(user.id, device="pytest-agent")


@pytest.fixture
def access_token(user):
    return JWT_Tools.create_access_token(user.id, user.username)


@pytest.fixture
def refresh_token(user, session):
    return JWT_Tools.create_refresh_token(user.id, user.username, session.id)


@pytest.fixture(autouse=True)
def override_jwt_settings(settings):
    settings.ACCESS_TOKEN_EXPIRE_MINUTES = 1
    settings.REFRESH_TOKEN_EXPIRE_DAYS = 1
    settings.JWT_SECRET = "testsecret123"
    settings.JWT_ALGORITHM = "HS256"
    settings.ROTATE_THRESHOLD_DAYS = 0.25


# -------------------------
# SUCCESS CASES
# -------------------------


@pytest.mark.django_db
def test_refresh_web_success(client, user, session, refresh_token, mocker, refresh_url):
    # Patch SessionManager.get_session to return our session
    mocker.patch.object(SessionManager, "get_session", return_value=session)

    response = client.post(
        refresh_url,
        {},
        HTTP_COOKIE=f"refresh={refresh_token}",
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert "access" in response.cookies
    assert response.data["message"] == "Token refreshed"


@pytest.mark.django_db
def test_refresh_android_success(
    client, user, session, refresh_token, mocker, refresh_url
):
    mocker.patch.object(SessionManager, "get_session", return_value=session)

    response = client.post(
        refresh_url,
        {"refresh": refresh_token},
        HTTP_X_CLIENT="android",
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert "access" in response.data
    assert "refresh" not in response.cookies
    access_payload = JWT_Tools.decode_token(response.data["access"])
    assert access_payload["sub"] == user.id


@pytest.mark.django_db
def test_refresh_rotates_token(
    client, user, session, refresh_token, mocker, refresh_url
):
    # Patch get_session
    mocker.patch.object(SessionManager, "get_session", return_value=session)

    # Patch JWT_Tools.should_rotate_refresh_token to always return True
    mocker.patch.object(JWT_Tools, "should_rotate_refresh_token", return_value=True)
    mocker.patch.object(
        JWT_Tools, "create_refresh_token", return_value="new_refresh_token"
    )

    response = client.post(
        refresh_url,
        {"refresh": refresh_token},
        HTTP_X_CLIENT="android",
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["access"] is not None
    assert response.data.get("refresh") == "new_refresh_token"


# -------------------------
# ERROR CASES
# -------------------------


@pytest.mark.django_db
def test_refresh_missing_token(client, refresh_url):
    response = client.post(refresh_url, {}, format="json")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data["error"] == "Refresh token missing"


@pytest.mark.django_db
def test_refresh_invalid_token(client, refresh_url):
    response = client.post(
        refresh_url,
        {"refresh": "invalid.token.here"},
        HTTP_X_CLIENT="android",
        format="json",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data["error"] == "Invalid token"


@pytest.mark.django_db
def test_refresh_expired_token(client, user, session, mocker, refresh_url):
    past_time = datetime.now(timezone.utc) - timedelta(days=1)
    payload = {
        "sub": user.id,
        "sid": session.id,
        "type": "refresh",
        "exp": past_time.timestamp(),
    }
    expired_token = jwt.encode(
        payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
    )

    mocker.patch.object(SessionManager, "get_session", return_value=session)

    response = client.post(
        refresh_url,
        {"refresh": expired_token},
        HTTP_X_CLIENT="android",
        format="json",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data["error"] == "Refresh token expired"


@pytest.mark.django_db
def test_refresh_invalid_user(client, session, refresh_url):
    # Create token with non-existing user ID
    payload = {
        "sub": 9999,
        "sid": session.id,
        "type": "refresh",
        "exp": (datetime.now(timezone.utc) + timedelta(days=1)).timestamp(),
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

    response = client.post(
        refresh_url,
        {"refresh": token},
        HTTP_X_CLIENT="android",
        format="json",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data["error"] == "Invalid credentials"


@pytest.mark.django_db
def test_refresh_invalid_session(client, user, refresh_url):
    # Create token with fake session ID
    payload = {
        "sub": user.id,
        "sid": "fake-session",
        "type": "refresh",
        "exp": (datetime.now(timezone.utc) + timedelta(days=1)).timestamp(),
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

    response = client.post(
        refresh_url,
        {"refresh": token},
        HTTP_X_CLIENT="android",
        format="json",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data["error"] == "Invalid credentials"
