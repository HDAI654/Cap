import logging
from datetime import datetime, timezone
from typing import Optional, List
from django.conf import settings
from redis.exceptions import RedisError
from core.crypto_utils import IDGenerator
from .redis_client import get_redis_client
from ....core.exceptions import SessionDoesNotExist, SessionStorageError

logger = logging.getLogger(__name__)
redis_client = get_redis_client()


class Session:
    def __init__(
        self,
        user_id: int,
        device: str,
        id: Optional[str] = None,
        created_at: Optional[datetime] = None,
    ):
        self.user_id = user_id
        self.device = device
        self.created_at = created_at or datetime.now(timezone.utc)
        self.id = id

        if not self.id:
            self._generate_id()

    def _generate_id(self):
        self.id = IDGenerator.random_hex(32)

    def delete(self):
        logger.info(
            "Starting session deletion session_id=%s user_id=%s",
            self.id,
            self.user_id,
        )
        pipe = redis_client.pipeline()
        pipe.multi()

        key_session = f"session:{self.id}"
        key_user_sessions = f"user:{self.user_id}"

        pipe.delete(key_session)
        pipe.lrem(key_user_sessions, 0, self.id)
        
        try:
            results = pipe.execute()
        except RedisError as e:
            logger.exception(
                "Failed to delete session session_id=%s user_id=%s", self.id, self.user_id,
            )
            raise SessionStorageError("Failed to delete session") from e

        deleted = results[0]
        removed = results[1]

        if deleted == 0:
            logger.warning("Session already deleted or never be exist")
            
        if removed == 0:
            logger.warning("Session not in user set or never be exist")
        
        logger.info("Session deleted successfully")
        return self 

    def save(self):
        logger.info(
            "Saving session session_id=%s user_id=%s",
            self.id,
            self.user_id,
        )

        pipe = redis_client.pipeline()
        pipe.multi()

        key_session = f"session:{self.id}"
        key_user_sessions = f"user:{self.user_id}"
        ttl_seconds = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60

        pipe.hset(
            key_session,
            mapping={
                "user_id": str(self.user_id),
                "device": self.device,
                "created_at": self.created_at.isoformat(),
            },
        )
        pipe.expire(key_session, ttl_seconds)
        
        pipe.sadd(key_user_sessions, self.id)
        pipe.expire(key_user_sessions, ttl_seconds)

        try:
            results = pipe.execute()
        except RedisError as e:
            logger.exception(
                "Failed to save session session_id=%s user_id=%s", self.id, self.user_id,
            )
            raise SessionStorageError("Failed to save session") from e
        
        logger.info("Session saved successfully")
        return self

    def __eq__(self, other):
        if not isinstance(other, Session):
            return False
        if self.id is None or other.id is None:
            return False
        return self.id == other.id
    
    def __hash__(self):
        return hash((self.id,))
    
    def __repr__(self):
        return f"Session(id={self.id}, user_id={self.user_id}, device={self.device}, created_at='{self.created_at}')"






class SessionManager:

    @staticmethod
    def get_session(session_id: str) -> Session:
        logger.info("Fetching session: session_id=%s", session_id)
        key_session = f"session:{session_id}"

        data = redis_client.hgetall(key_session)

        if not data:
            logger.debug("Session not found: key=%s", key_session)
            raise SessionDoesNotExist(f"Session not found: key={key_session}")

        try:
            user_id = int(data[b"user_id"].decode())
            device = data[b"device"].decode()
            created_at = datetime.fromisoformat(data[b"created_at"].decode())
        except (KeyError, ValueError, TypeError) as e:
            logger.error(
                "Failed decoding session hash fields: key=%s error=%s", key_session, e
            )
            raise SessionStorageError(
                f"Corrupted session data for session_id={session_id}"
            )

        logger.debug("Successfully reconstructed session: session_id=%s", session_id)

        return Session(
            id=session_id,
            user_id=user_id,
            device=device,
            created_at=created_at,
        )

    @staticmethod
    def get_user_sessions(user_id: int) -> List[Session]:
        key_user_sessions = f"user:{user_id}"
        logger.info("Fetching user sessions: user_id=%s", user_id)

        try:
            session_ids = redis_client.lrange(key_user_sessions, 0, -1)
        except RedisError as e:
            logger.error(
                "Failed fetching user session list: key=%s error=%s",
                key_user_sessions,
                e,
            )
            raise SessionStorageError("Failed fetching user sessions")

        sessions = []
        for sid_bytes in session_ids:
            sid = sid_bytes.decode()
            logger.debug("Processing session_id=%s for user_id=%s", sid, user_id)

            session = SessionManager.get_session(sid)
            sessions.append(session)

        logger.info(
            "Completed fetching user sessions: user_id=%s total_sessions=%s",
            user_id,
            len(sessions),
        )
        return sessions

    @staticmethod
    def new_session(user_id: int, device: str) -> Session:
        return Session(user_id=user_id, device=device)
