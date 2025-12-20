import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
import jwt

from accounts.services.jwt_service import JWT_Tools

User = get_user_model()


@pytest.fixture
def revoke_url():
    return reverse("revoke")


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="testuser",
        password="StrongPassword123!",
        email="test@example.com",
    )


@pytest.fixture
def access_token(user):
    return JWT_Tools.create_access_token(user.id, user.username)


@pytest.fixture
def session(mocker, user):
    session = mocker.Mock()
    session.id = 123
    session.user_id = user.id
    return session


# ---------------------------------------------------------------------
# SUCCESS CASES
# ---------------------------------------------------------------------


@pytest.mark.django_db
def test_revoke_success_android(
    client, mocker, revoke_url, user, access_token, session
):
    """
    ANDROID:
    - access token in JSON
    - session revoked successfully
    """

    mocker.patch(
        "accounts.views.SessionManager.get_session",
        return_value=session,
    )

    response = client.post(
        revoke_url,
        data={
            "access": access_token,
            "sid": session.id,
        },
        format="json",
        HTTP_X_CLIENT="android",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data == {"success": "Logout successful"}

    session.delete.assert_called_once()


@pytest.mark.django_db
def test_revoke_success_web(client, mocker, revoke_url, user, access_token, session):
    """
    WEB:
    - access token in cookie
    - session revoked successfully
    """

    mocker.patch(
        "accounts.views.SessionManager.get_session",
        return_value=session,
    )

    client.cookies["access"] = access_token

    response = client.post(
        revoke_url,
        data={"sid": session.id},
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data == {"success": "Logout successful"}

    session.delete.assert_called_once()


# ---------------------------------------------------------------------
# ERROR CASES
# ---------------------------------------------------------------------


@pytest.mark.django_db
def test_revoke_missing_access_token(client, revoke_url):
    response = client.post(revoke_url, data={"sid": 1}, format="json")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data == {"error": "Access token missing"}


@pytest.mark.django_db
def test_revoke_invalid_access_token(client, revoke_url):
    response = client.post(
        revoke_url,
        data={"access": "invalid.token", "sid": 1},
        format="json",
        HTTP_X_CLIENT="android",
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data == {"error": "Invalid access token"}


@pytest.mark.django_db
def test_revoke_non_integer_session_id(client, revoke_url, access_token):
    response = client.post(
        revoke_url,
        data={"access": access_token, "sid": "abc"},
        format="json",
        HTTP_X_CLIENT="android",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data == {"error": "session id must be integer"}


@pytest.mark.django_db
def test_revoke_session_not_found(client, mocker, revoke_url, access_token):
    mocker.patch(
        "accounts.views.SessionManager.get_session",
        return_value=None,
    )

    response = client.post(
        revoke_url,
        data={"access": access_token, "sid": 999},
        format="json",
        HTTP_X_CLIENT="android",
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data == {"error": "Invalid credentials"}


@pytest.mark.django_db
def test_revoke_session_wrong_user(client, mocker, revoke_url, user, access_token):
    other_session = mocker.Mock()
    other_session.user_id = user.id + 999

    mocker.patch(
        "accounts.views.SessionManager.get_session",
        return_value=other_session,
    )

    response = client.post(
        revoke_url,
        data={"access": access_token, "sid": 1},
        format="json",
        HTTP_X_CLIENT="android",
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data == {"error": "Invalid credentials"}


@pytest.mark.django_db
def test_revoke_expired_access_token(client, revoke_url, settings):
    expired_payload = {
        "sub": 1,
        "type": "access",
        "exp": 0,
    }
    expired_token = jwt.encode(
        expired_payload,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )

    response = client.post(
        revoke_url,
        data={"access": expired_token, "sid": 1},
        format="json",
        HTTP_X_CLIENT="android",
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data == {"error": "Access token expired"}
