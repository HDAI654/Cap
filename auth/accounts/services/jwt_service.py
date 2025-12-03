import jwt
from datetime import datetime, timedelta
from django.conf import settings


class JWT_Tools:

    @staticmethod
    def create_access_token(user_id, username):
        exp = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        payload = {
            "sub": user_id,
            "username": username,
            "exp": exp,
            "type": "access"
        }
        return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    
    @staticmethod
    def create_refresh_token(user_id, username, session_id):
        exp = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        payload = {
            "sid": session_id,
            "sub": user_id,
            "username": username,
            "exp": exp,
            "type": "refresh"
        }
        return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

    @staticmethod
    def decode_token(token):
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
