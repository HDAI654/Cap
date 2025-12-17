from datetime import datetime, timedelta, timezone
import jwt
from django.conf import settings


class JWT_Tools:
    @staticmethod
    def create_access_token(user_id, username):
        exp = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        payload = {"sub": user_id, "username": username, "exp": exp, "type": "access"}
        return jwt.encode(
            payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
        )

    @staticmethod
    def create_refresh_token(user_id, username, session_id):
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
    def should_rotate_refresh_token(
        token: str, rotate_threshold: timedelta = timedelta(days=1)
    ) -> bool:
        """
        Determines if a refresh token should be rotated based on its expiration.

        Args:
            token: JWT refresh token.
            rotate_threshold: Time delta before expiration to trigger rotation (default 1 day).

        Returns:
            True if the token is near expiration and should be rotated, False otherwise.
        """
        payload = JWT_Tools.decode_token(token)
        if payload.get("type") != "refresh":
            raise ValueError("Token is not a refresh token")

        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        now = datetime.now(timezone.utc)

        # Rotate if the token will expire within the threshold
        return exp - now <= rotate_threshold
