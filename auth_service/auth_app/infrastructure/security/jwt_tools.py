from datetime import datetime, timedelta, timezone
import jwt
from django.conf import settings


class JWT_Tools:
    @staticmethod
    def create_access_token(user_id: str, username: str) -> str:
        exp = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        payload = {"sub": user_id, "username": username, "exp": exp, "type": "access"}
        return jwt.encode(
            payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
        )

    @staticmethod
    def create_refresh_token(user_id: str, username: str, session_id: str):
        exp = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        payload = {
            "sid": session_id,
            "sub": user_id,
            "username": username,
            "exp": exp,
            "type": "refresh",
        }
        return jwt.encode(
            payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
        )

    @staticmethod
    def decode_token(token):
        return jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )

    @staticmethod
    def should_rotate_refresh_token(token_expire_time: str) -> bool:
        rotate_threshold = timedelta(days=settings.ROTATE_THRESHOLD_DAYS)

        exp = datetime.fromtimestamp(token_expire_time, tz=timezone.utc)
        now = datetime.now(timezone.utc)

        # Rotate if the token will expire within the threshold
        return exp - now <= rotate_threshold
