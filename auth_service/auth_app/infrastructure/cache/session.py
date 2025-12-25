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
        key_session = f"session:{self.id}"
        key_user_sessions = f"user:{self.user_id}"

        try:
            deleted_hash = redis_client.delete(key_session)
        except RedisError as e:
            logger.error(
                "Failed deleting session hash: key=%s error=%s", key_session, e
            )
            raise SessionStorageError("Failed to delete session")

        try:
            removed = redis_client.lrem(key_user_sessions, 0, self.id)
            logger.debug(
                "Removed session ID from user list: key=%s removed=%s",
                key_user_sessions,
                removed,
            )
        except RedisError as e:
            logger.error(
                "Failed removing session from user session list: key=%s session_id=%s error=%s",
                key_user_sessions,
                self.id,
                e,
            )
            raise SessionStorageError("Failed to delete session from user list")

    def save(self):
        key_session = f"session:{self.id}"
        key_user_sessions = f"user:{self.user_id}"
        ttl_seconds = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60

        logger.info(
            "Saving session: session_id=%s user_id=%s device=%s ttl=%s",
            self.id,
            self.user_id,
            self.device,
            ttl_seconds,
        )

        try:
            redis_client.hset(
                key_session,
                mapping={
                    "user_id": str(self.user_id),
                    "device": self.device,
                    "created_at": self.created_at.isoformat(),
                },
            )
            redis_client.expire(key_session, ttl_seconds)
            logger.debug("Saved session hash and set TTL: key=%s", key_session)
        except RedisError as e:
            logger.error("Failed saving session hash: key=%s error=%s", key_session, e)
            raise SessionStorageError("Failed to save session")

        try:
            redis_client.rpush(key_user_sessions, self.id)
            redis_client.expire(key_user_sessions, ttl_seconds)
            logger.debug(
                "Pushed session ID to user list and set TTL: key=%s session_id=%s",
                key_user_sessions,
                self.id,
            )
        except RedisError as e:
            logger.error(
                "Failed pushing session to user list: key=%s session_id=%s error=%s",
                key_user_sessions,
                self.id,
                e,
            )
            raise SessionStorageError("Failed to push session to user list")

        return self


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
