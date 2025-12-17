import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status

from accounts.services.jwt_service import JWT_Tools

User = get_user_model()


@pytest.fixture
def login_url():
    return reverse("login")


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="testuser",
        password="StrongPassword123!",
        email="testuser@example.com",
    )


@pytest.fixture
def valid_payload():
    return {
        "username": "testuser",
        "password": "StrongPassword123!",
    }


# ---------------------------------------------------------------------
# SUCCESS CASES
# ---------------------------------------------------------------------


@pytest.mark.django_db
def test_login_success_web(client, user, mocker, login_url, valid_payload):
    """
    WEB client:
    - cookies set
    - no tokens in JSON
    - session created
    """

    mocker.patch(
        "accounts.views.authenticate",
        return_value=user,
    )

    response = client.post(
        login_url,
        valid_payload,
        format="json",
        HTTP_USER_AGENT="pytest-agent",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data == {"message": "User created successfully"}

    # Cookies
    assert "access" in response.cookies
    assert "refresh" in response.cookies

    access = response.cookies["access"].value
    refresh = response.cookies["refresh"].value

    access_payload = JWT_Tools.decode_token(access)
    refresh_payload = JWT_Tools.decode_token(refresh)

    assert access_payload["sub"] == user.id
    assert refresh_payload["type"] == "refresh"


@pytest.mark.django_db
def test_login_success_android(client, user, mocker, login_url, valid_payload):
    """
    ANDROID client:
    - tokens returned in JSON
    - no cookies
    """

    mocker.patch(
        "accounts.views.authenticate",
        return_value=user,
    )

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
    assert response.data["message"] == "User created successfully"

    assert "access" not in response.cookies
    assert "refresh" not in response.cookies

    access_payload = JWT_Tools.decode_token(response.data["access"])
    refresh_payload = JWT_Tools.decode_token(response.data["refresh"])

    assert access_payload["username"] == user.username
    assert refresh_payload["type"] == "refresh"


# ---------------------------------------------------------------------
# ERROR CASES
# ---------------------------------------------------------------------


@pytest.mark.django_db
def test_login_invalid_credentials(client, mocker, login_url, valid_payload):
    """
    Invalid username/password → 401
    """

    mocker.patch(
        "accounts.views.authenticate",
        return_value=None,
    )

    response = client.post(
        login_url,
        valid_payload,
        format="json",
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data == {"error": "Invalid credentials"}


@pytest.mark.django_db
def test_login_validation_error(client, login_url):
    """
    Serializer validation error → 400
    """

    response = client.post(
        login_url,
        {"username": "", "password": ""},
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert isinstance(response.data, dict)


@pytest.mark.django_db
def test_login_internal_error(client, user, mocker, login_url, valid_payload):
    """
    Unexpected exception → 500
    """

    mocker.patch(
        "accounts.views.authenticate",
        side_effect=Exception("Auth failure"),
    )

    response = client.post(
        login_url,
        valid_payload,
        format="json",
    )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.data == {"error": "Failed to login"}
