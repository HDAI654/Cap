from ..utils.crypto_utils import IDGenerator
from .redis_client import get_redis_client
from datetime import datetime
from typing import Optional, List
from django.conf import settings

redis_client = get_redis_client()

class Session:
    def __init__(self, user_id:int, device:str, id:str = None, created_at:Optional[str]=None):
        self.user_id = user_id
        self.device = device
        self.created_at = created_at or datetime.utcnow()
        self.id = id or self._generate_id()

    @classmethod
    def _generate_id(self):
        id = IDGenerator.random_hex(32)
        return id
    
    def revoke(self):
        pass

    def delete(self):
        key_session = f"session:{self.id}"
        key_user_sessions = f"user:{self.user_id}"

        # 1️⃣ Remove session hash
        redis_client.delete(key_session)

        # 2️⃣ Remove this session ID from the user's session list
        redis_client.lrem(key_user_sessions, 0, self.id)

    def save(self):
        key_session = f"session:{self.id}"
        key_user_sessions = f"user:{self.user_id}"
        ttl_seconds = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60

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
    def get_session(session_id: str) -> Optional[Session]:
        """
        Retrieve a single session by its ID.
        Returns None if the session does not exist.
        """
        key_session = f"session:{session_id}"
        data = redis_client.hgetall(key_session)

        if not data:
            return None  # session not found

        # Redis returns bytes, decode them
        user_id = int(data[b"user_id"].decode())
        device = data[b"device"].decode()
        created_at = datetime.fromisoformat(data[b"created_at"].decode())

        # Recreate Session object with existing ID
        session = Session(id=session_id, user_id=user_id, device=device, created_at=created_at)
        return session

    @staticmethod
    def get_user_sessions(user_id: int) -> List[Session]:
        """
        Retrieve all sessions for a given user.
        Returns empty list if no sessions found.
        """
        key_user_sessions = f"user:{user_id}"
        session_ids = redis_client.lrange(key_user_sessions, 0, -1)

        sessions = []
        for sid_bytes in session_ids:
            sid = sid_bytes.decode()
            session = SessionManager.get_session(sid)
            if session:
                sessions.append(session)

        return sessions
    
