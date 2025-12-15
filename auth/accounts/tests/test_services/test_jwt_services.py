import pytest
import jwt
from datetime import datetime, timedelta
from django.conf import settings
from ...services.jwt_service import JWT_Tools


@pytest.fixture(autouse=True)
def override_jwt_settings(settings):
    """Override JWT settings for tests."""
    settings.ACCESS_TOKEN_EXPIRE_MINUTES = 1
    settings.REFRESH_TOKEN_EXPIRE_DAYS = 1
    settings.JWT_SECRET = "testsecret123"
    settings.JWT_ALGORITHM = "HS256"


@pytest.mark.django_db
def test_create_access_token():
    user_id = 42
    username = "testuser"
    token = JWT_Tools.create_access_token(user_id, username)
    assert isinstance(token, str)

    decoded = jwt.decode(
        token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
    )
    assert decoded["sub"] == user_id
    assert decoded["username"] == username
    assert decoded["type"] == "access"
    assert "exp" in decoded
    assert datetime.utcfromtimestamp(decoded["exp"]) > datetime.utcnow()


@pytest.mark.django_db
def test_create_refresh_token():
    user_id = 42
    username = "testuser"
    session_id = "session_abc123"
    token = JWT_Tools.create_refresh_token(user_id, username, session_id)
    assert isinstance(token, str)

    decoded = jwt.decode(
        token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
    )
    assert decoded["sub"] == user_id
    assert decoded["username"] == username
    assert decoded["sid"] == session_id
    assert decoded["type"] == "refresh"
    assert "exp" in decoded
    assert datetime.utcfromtimestamp(decoded["exp"]) > datetime.utcnow()


@pytest.mark.django_db
def test_decode_token():
    user_id = 1
    username = "decode_test"
    token = JWT_Tools.create_access_token(user_id, username)
    decoded = JWT_Tools.decode_token(token)
    assert decoded["sub"] == user_id
    assert decoded["username"] == username
    assert decoded["type"] == "access"


@pytest.mark.django_db
def test_invalid_token():
    invalid_token = "this.is.not.a.jwt"
    with pytest.raises(jwt.exceptions.DecodeError):
        JWT_Tools.decode_token(invalid_token)


@pytest.mark.django_db
def test_expired_token():
    # Create a token that is already expired
    past_time = datetime.utcnow() - timedelta(minutes=10)
    payload = {
        "sub": 1,
        "username": "expired_user",
        "exp": past_time,
        "type": "access",
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

    with pytest.raises(jwt.exceptions.ExpiredSignatureError):
        JWT_Tools.decode_token(token)
