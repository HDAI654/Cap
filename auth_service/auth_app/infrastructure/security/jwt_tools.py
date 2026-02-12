from datetime import datetime, timedelta, timezone
import jwt
from auth_app.domain.value_objects.id import ID
from auth_app.domain.value_objects.username import Username
from auth_app.domain.value_objects.datetime import DateTime
from django.conf import settings


class JWT_Tools:
    @staticmethod
    def create_access_token(user_id: ID, username: Username) -> str:
        exp = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        exp = exp.timestamp()
        payload = {"sub": user_id.value, "username": username.value, "exp": exp, "type": "access"}
        return jwt.encode(
            payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
        )

    @staticmethod
    def create_refresh_token(user_id: ID, username: Username, session_id: ID) -> str:
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

    @staticmethod
    def decode_token(token):
        return jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )

    @staticmethod
    def should_rotate_refresh_token(token_expire_time: DateTime) -> bool:
        rotate_threshold = timedelta(days=settings.ROTATE_THRESHOLD_DAYS)

        exp = datetime.fromtimestamp(token_expire_time.value, timezone.utc)
        now = datetime.now(timezone.utc)

        return exp - now <= rotate_threshold
