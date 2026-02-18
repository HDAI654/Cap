from datetime import datetime, timedelta, timezone
import jwt
from jwt import ExpiredSignatureError, InvalidTokenError, DecodeError
from core.exceptions import InvalidToken, TokenCreationError
from auth_app.domain.value_objects.id import ID
from auth_app.domain.value_objects.username import Username
from auth_app.domain.value_objects.datetime import DateTime
from django.conf import settings


class JWT_Tools:
    @staticmethod
    def create_access_token(user_id: ID, username: Username) -> str:
        try:
            exp = datetime.now(timezone.utc) + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
            exp = exp.timestamp()
            payload = {
                "sub": user_id.value,
                "username": username.value,
                "exp": exp,
                "type": "access",
            }
            return jwt.encode(
                payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
            )
        except Exception as e:
            raise TokenCreationError(
                f"Unexpected error occurred during access-token generation:\n{str(e)}"
            ) from e

    @staticmethod
    def create_refresh_token(user_id: ID, username: Username, session_id: ID) -> str:
        try:
            exp = datetime.now(timezone.utc) + timedelta(
                days=settings.REFRESH_TOKEN_EXPIRE_DAYS
            )
            exp = exp.timestamp()
            payload = {
                "sid": session_id.value,
                "sub": user_id.value,
                "username": username.value,
                "exp": exp,
                "type": "refresh",
            }
            return jwt.encode(
                payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
            )
        except Exception as e:
            raise TokenCreationError(
                f"Unexpected error occurred during refresh-token generation:\n{str(e)}"
            ) from e

    @staticmethod
    def decode_token(token):
        try:
            return jwt.decode(
                token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
            )
        except ExpiredSignatureError:
            raise InvalidToken("Token has expired")
        except (InvalidTokenError, DecodeError):
            raise InvalidToken("Token is malformed or signature is invalid")

    @staticmethod
    def should_rotate_refresh_token(token_expire_time: DateTime) -> bool:
        rotate_threshold = timedelta(days=settings.ROTATE_THRESHOLD_DAYS)

        exp = datetime.fromtimestamp(token_expire_time.value, timezone.utc)
        now = datetime.now(timezone.utc)

        return exp - now <= rotate_threshold
