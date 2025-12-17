import logging
from datetime import datetime, timezone
from typing import Optional, List
from django.conf import settings
from ..utils.crypto_utils import IDGenerator
from .redis_client import get_redis_client

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
            logger.debug("No session ID provided; generating a new one.")
            self._generate_id()

    def _generate_id(self):
        self.id = IDGenerator.random_hex(32)
        logger.debug("Generated new session ID: %s", self.id)

    def revoke(self):
        logger.info(
            "Revoking session: session_id=%s user_id=%s device=%s",
            self.id,
            self.user_id,
            self.device,
        )

        self.delete()
        self._generate_id()
        self.created_at = datetime.now(timezone.utc)
        self.save()
        return self

    def delete(self):
        key_session = f"session:{self.id}"
        key_user_sessions = f"user:{self.user_id}"

        logger.info(
            "Deleting session: session_key=%s user_sessions_key=%s session_id=%s",
            key_session,
            key_user_sessions,
            self.id,
        )

        try:
            deleted_hash = redis_client.delete(key_session)
            logger.debug(
                "Deleted session hash: key=%s deleted=%s",
                key_session,
                bool(deleted_hash),
            )
        except Exception as e:
            logger.error(
                "Failed deleting session hash: key=%s error=%s", key_session, e
            )

        try:
            removed = redis_client.lrem(key_user_sessions, 0, self.id)
            logger.debug(
                "Removed session ID from user list: key=%s removed=%s",
                key_user_sessions,
                removed,
            )
        except Exception as e:
            logger.error(
                "Failed removing session from user session list: key=%s session_id=%s error=%s",
                key_user_sessions,
                self.id,
                e,
            )

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
        except Exception as e:
            logger.error("Failed saving session hash: key=%s error=%s", key_session, e)

        try:
            redis_client.rpush(key_user_sessions, self.id)
            redis_client.expire(key_user_sessions, ttl_seconds)
            logger.debug(
                "Pushed session ID to user list and set TTL: key=%s session_id=%s",
                key_user_sessions,
                self.id,
            )
        except Exception as e:
            logger.error(
                "Failed pushing session to user list: key=%s session_id=%s error=%s",
                key_user_sessions,
                self.id,
                e,
            )

        return self


class SessionManager:

    @staticmethod
    def get_session(session_id: str) -> Optional[Session]:
        logger.info("Fetching session: session_id=%s", session_id)
        key_session = f"session:{session_id}"

        try:
            data = redis_client.hgetall(key_session)
        except Exception as e:
            logger.error("Failed to fetch session: key=%s error=%s", key_session, e)
            return None

        if not data:
            logger.debug("Session not found: key=%s", key_session)
            return None

        try:
            user_id = int(data[b"user_id"].decode())
            device = data[b"device"].decode()
            created_at = datetime.fromisoformat(data[b"created_at"].decode())
        except Exception as e:
            logger.error(
                "Failed decoding session hash fields: key=%s error=%s", key_session, e
            )
            return None

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
        except Exception as e:
            logger.error(
                "Failed fetching user session list: key=%s error=%s",
                key_user_sessions,
                e,
            )
            return []

        sessions = []
        for sid_bytes in session_ids:
            sid = sid_bytes.decode()
            logger.debug("Processing session_id=%s for user_id=%s", sid, user_id)

            session = SessionManager.get_session(sid)
            if session:
                sessions.append(session)
            else:
                logger.warning(
                    "Session ID referenced in user list but not found: user_id=%s session_id=%s",
                    user_id,
                    sid,
                )

        logger.info(
            "Completed fetching user sessions: user_id=%s total_sessions=%s",
            user_id,
            len(sessions),
        )
        return sessions

    @staticmethod
    def new_session(user_id: int, device: str) -> Session:
        return Session(user_id=user_id, device=device)
