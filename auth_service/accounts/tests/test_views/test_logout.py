import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from accounts.services.jwt_service import JWT_Tools
from accounts.services.session_service import SessionManager
import jwt

User = get_user_model()


@pytest.fixture
def logout_url():
    return reverse("logout")


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="testuser",
        email="testuser@example.com",
        password="StrongPassword123!",
    )


@pytest.fixture
def valid_session(user):
    session = SessionManager.new_session(user.id, "pytest-agent")
    session.save()
    return session


@pytest.mark.django_db
def test_logout_success_web(client, user, valid_session, logout_url, mocker):
    # Patch JWT decode to return valid payload
    mocker.patch(
        "accounts.views.JWT_Tools.decode_token",
        return_value={
            "sub": user.id,
            "sid": valid_session.id,
            "type": "refresh",
        },
    )

    # Patch SessionManager.get_session to return our session
    mocker.patch(
        "accounts.views.SessionManager.get_session",
        return_value=valid_session,
    )

    # Patch session.delete to avoid touching Redis
    mock_delete = mocker.patch.object(valid_session, "delete")

    # Simulate web client with refresh token in cookie
    client.cookies["refresh"] = "dummy_refresh_token"

    response = client.post(logout_url, HTTP_USER_AGENT="pytest-agent")

    assert response.status_code == status.HTTP_200_OK
    assert response.data == {"success": "Logout successful"}
    mock_delete.assert_called_once()
    # Check that cookies are deleted
    assert "refresh" not in response.cookies or response.cookies["refresh"].value == ""
    assert "access" not in response.cookies or response.cookies["access"].value == ""


@pytest.mark.django_db
def test_logout_success_android(client, user, valid_session, logout_url, mocker):
    # Patch JWT decode
    mocker.patch(
        "accounts.views.JWT_Tools.decode_token",
        return_value={
            "sub": user.id,
            "sid": valid_session.id,
            "type": "refresh",
        },
    )
    mocker.patch(
        "accounts.views.SessionManager.get_session",
        return_value=valid_session,
    )
    mock_delete = mocker.patch.object(valid_session, "delete")

    response = client.post(
        logout_url,
        {"refresh": "dummy_refresh_token"},
        format="json",
        HTTP_X_CLIENT="android",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data == {"success": "Logout successful"}
    mock_delete.assert_called_once()


@pytest.mark.django_db
def test_logout_missing_token(client, logout_url):
    response = client.post(logout_url, format="json")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data == {"error": "Refresh token missing"}


@pytest.mark.django_db
def test_logout_invalid_token_payload(client, user, valid_session, logout_url, mocker):
    mocker.patch(
        "accounts.views.JWT_Tools.decode_token",
        return_value={"sub": user.id, "sid": valid_session.id},  # missing 'type'
    )
    response = client.post(
        logout_url,
        {"refresh": "dummy_refresh_token"},
        format="json",
        HTTP_X_CLIENT="android",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data == {"error": "Invalid refresh token"}


@pytest.mark.django_db
def test_logout_user_not_found(client, valid_session, logout_url, mocker):
    mocker.patch(
        "accounts.views.JWT_Tools.decode_token",
        return_value={
            "sub": 9999,  # non-existent user
            "sid": valid_session.id,
            "type": "refresh",
        },
    )
    response = client.post(
        logout_url,
        {"refresh": "dummy_refresh_token"},
        format="json",
        HTTP_X_CLIENT="android",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data == {"error": "Invalid credentials"}


@pytest.mark.django_db
def test_logout_session_not_found(client, user, logout_url, mocker):
    mocker.patch(
        "accounts.views.JWT_Tools.decode_token",
        return_value={
            "sub": user.id,
            "sid": "nonexistent_session",
            "type": "refresh",
        },
    )
    mocker.patch(
        "accounts.views.SessionManager.get_session",
        return_value=None,
    )
    response = client.post(
        logout_url,
        {"refresh": "dummy_refresh_token"},
        format="json",
        HTTP_X_CLIENT="android",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data == {"error": "Invalid credentials"}


@pytest.mark.django_db
def test_logout_expired_token(client, logout_url, mocker):
    mocker.patch(
        "accounts.views.JWT_Tools.decode_token",
        side_effect=jwt.ExpiredSignatureError,
    )
    response = client.post(
        logout_url,
        {"refresh": "dummy_refresh_token"},
        format="json",
        HTTP_X_CLIENT="android",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data == {"error": "Refresh token expired"}


@pytest.mark.django_db
def test_logout_internal_error(client, user, valid_session, logout_url, mocker):
    mocker.patch(
        "accounts.views.JWT_Tools.decode_token",
        side_effect=Exception("Random failure"),
    )
    response = client.post(
        logout_url,
        {"refresh": "dummy_refresh_token"},
        format="json",
        HTTP_X_CLIENT="android",
    )
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.data == {"error": "INTERNAL SERVER ERROR"}
