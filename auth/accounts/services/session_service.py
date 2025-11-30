from ..utils.crypto_utils import IDGenerator
from .redis_client import get_redis_client
from datetime import datetime
from typing import Optional
from django.conf import settings

redis_client = get_redis_client()

class Session:
    def __init__(self, user_id:int, device:str, created_at:Optional[str]=None):
        self.user_id = user_id
        self.device = device
        self.created_at = created_at or datetime.utcnow()
        self.id = self._generate_id()

    @classmethod
    def _generate_id(self):
        id = IDGenerator.random_hex(32)
        return id
    
    def revoke(self):
        pass

    def delete(self):
        pass

    def save(self):
        key_session = f"session:{self.id}"
        key_user_sessions = f"user:{self.user_id}"
        ttl_seconds = settings.REFRESH_TOKEN_EXPIRE_DAYS

        # 1️⃣ Store session hash
        redis_client.hset(
            key_session,
            mapping={
                "user_id": str(self.user_id),
                "device": self.device,
                "created_at": self.created_at.isoformat()
            }
        )
        redis_client.expire(key_session, ttl_seconds)

        # 2️⃣ Add session ID to user's session list
        redis_client.rpush(key_user_sessions, self.id)
        redis_client.expire(key_user_sessions, ttl_seconds)

        return self
    
class SessionManager:

    @staticmethod
    def get(id:str) -> Session | None:
        pass
