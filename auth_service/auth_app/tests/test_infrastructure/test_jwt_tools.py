import pytest
from datetime import datetime, timedelta, timezone
from django.conf import settings
import jwt
from auth_app.infrastructure.security.jwt_tools import JWT_Tools

class TestsJWT_Tools:
    @pytest.fixture(autouse=True)
    def jwt_settings(self, settings):
        settings.JWT_SECRET = "test-secret"
        settings.JWT_ALGORITHM = "HS256"
        settings.ACCESS_TOKEN_EXPIRE_MINUTES = 15
        settings.REFRESH_TOKEN_EXPIRE_DAYS = 7
        settings.ROTATE_THRESHOLD_DAYS = 2

    def test_create_access_token_payload(self):
        token = JWT_Tools.create_access_token(user_id="TestUserID-mefenifeui-ekfne", username="hamed")
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )

        assert payload["sub"] == "TestUserID-mefenifeui-ekfne"
        assert payload["username"] == "hamed"
        assert payload["type"] == "access"
        assert payload["exp"] > datetime.now(timezone.utc).timestamp()

    def test_create_refresh_token_payload(self):
        token = JWT_Tools.create_refresh_token(
            user_id="TestUserID-mefenifeui-ekfne", username="hamed", session_id="session-123"
        )
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )

        assert payload["sub"] == "TestUserID-mefenifeui-ekfne"
        assert payload["username"] == "hamed"
        assert payload["sid"] == "session-123"
        assert payload["type"] == "refresh"
        assert payload["exp"] > datetime.now(timezone.utc).timestamp()

    def test_decode_token_returns_payload(self):
        token = JWT_Tools.create_access_token(user_id="TestUserID-qwidojqid-ekaioneoiefhnh", username="user42")
        payload = JWT_Tools.decode_token(token)

        assert payload["sub"] == "TestUserID-qwidojqid-ekaioneoiefhnh"
        assert payload["username"] == "user42"
        assert payload["type"] == "access"

    def test_decode_token_invalid_token(self):
        with pytest.raises(jwt.InvalidTokenError):
            JWT_Tools.decode_token("this.is.not.a.valid.jwt")

    def test_decode_token_expired_token(self):
        exp = datetime.now(timezone.utc) - timedelta(minutes=1)
        payload = {
            "sub": "expired-user",
            "username": "hamed",
            "exp": exp,
            "type": "access",
        }
        token = jwt.encode(
            payload,
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM,
        )

        with pytest.raises(jwt.ExpiredSignatureError):
            JWT_Tools.decode_token(token)

    def test_decode_token_invalid_signature(self):
        payload = {
            "sub": "user-123",
            "username": "hamed",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
            "type": "access",
        }
        token = jwt.encode(
            payload,
            "wrong-secret",
            algorithm=settings.JWT_ALGORITHM,
        )

        with pytest.raises(jwt.InvalidSignatureError):
            JWT_Tools.decode_token(token)

    def test_should_rotate_refresh_token_true(self):
        exp = datetime.now(timezone.utc) + timedelta(days=1)
        assert JWT_Tools.should_rotate_refresh_token(exp.timestamp()) is True

    def test_should_rotate_refresh_token_false(self):
        exp = datetime.now(timezone.utc) + timedelta(days=10)
        assert JWT_Tools.should_rotate_refresh_token(exp.timestamp()) is False

