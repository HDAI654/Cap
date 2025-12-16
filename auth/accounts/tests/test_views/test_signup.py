import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from ...services.jwt_service import JWT_Tools
from ...services.session_service import Session

User = get_user_model()


@pytest.fixture
def signup_url():
    return reverse("signup")


@pytest.fixture
def valid_payload():
    return {
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "StrongPassword123!",
    }


@pytest.fixture
def session(patch_redis):
    return Session(user_id=1, device="pytest-agent")


@pytest.mark.django_db
def test_signup_success_web(client, mocker, signup_url, valid_payload):
    """
    WEB client:
    - user created
    - cookies set
    - no tokens in JSON body
    """

    mocker.patch("accounts.services.user_services.publish_user_created")

    response = client.post(
        signup_url,
        valid_payload,
        format="json",
        HTTP_USER_AGENT="pytest-agent",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data == {"message": "User created successfully"}

    # --- User created ---
    user = User.objects.get(username="testuser")
    assert user.email == "testuser@example.com"

    # --- Cookies set ---
    assert "access" in response.cookies
    assert "refresh" in response.cookies

    access_token = response.cookies["access"].value
    refresh_token = response.cookies["refresh"].value

    # --- Tokens valid ---
    access_payload = JWT_Tools.decode_token(access_token)
    refresh_payload = JWT_Tools.decode_token(refresh_token)

    assert access_payload["sub"] == user.id
    assert refresh_payload["sub"] == user.id
    assert refresh_payload["type"] == "refresh"


@pytest.mark.django_db
def test_signup_success_android(client, mocker, signup_url, valid_payload):
    """
    ANDROID client:
    - tokens returned in JSON
    - no cookies
    """

    mocker.patch("accounts.services.user_services.publish_user_created")

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
    assert response.data["message"] == "User created successfully"

    # --- No cookies ---
    assert "access" not in response.cookies
    assert "refresh" not in response.cookies

    # --- Tokens valid ---
    access_payload = JWT_Tools.decode_token(response.data["access"])
    refresh_payload = JWT_Tools.decode_token(response.data["refresh"])

    assert access_payload["username"] == "testuser"
    assert refresh_payload["type"] == "refresh"


@pytest.mark.django_db
def test_signup_validation_error(client, signup_url):
    """
    Invalid payload returns 400 with serializer errors.
    """
    response = client.post(
        signup_url,
        {"username": "", "email": "invalid", "password": ""},
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert isinstance(response.data, dict)


@pytest.mark.django_db
def test_signup_internal_error(client, mocker, signup_url, valid_payload):
    """
    Unexpected exception returns HTTP 500.
    """

    mocker.patch(
        "accounts.views.create_user",
        side_effect=Exception("DB failure"),
    )

    response = client.post(
        signup_url,
        valid_payload,
        format="json",
    )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.data == {"error": "Failed to create user"}


@pytest.mark.django_db
def test_signup_requires_post_method(client, signup_url):
    """
    GET method is not allowed.
    """
    response = client.get(signup_url)
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
def test_signup_creates_session(client, session, mocker, signup_url, valid_payload):
    # Prepare a mock session
    session.save = mocker.Mock()

    # Patch the SessionManager to return our mock
    mocker.patch(
        "accounts.views.SessionManager.new_session",
        return_value=session,
    )

    # Call the signup endpoint
    response = client.post(
        signup_url,
        valid_payload,
        format="json",
        HTTP_USER_AGENT="pytest-agent",
    )

    # --- Assertions ---
    assert response.status_code == 200
    session.save.assert_called_once()
