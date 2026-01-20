import logging
from typing import List
from django.conf import settings
from redis.exceptions import RedisError
from core.exceptions import SessionDoesNotExist, SessionStorageError
from auth_app.domain.entities.session import SessionEntity
from auth_app.domain.factories.session_factory import SessionFactory
from auth_app.domain.ports.session_repository import SessionRepository
from auth_app.domain.value_objects.id import ID

logger = logging.getLogger(__name__)


class RedisSessionRepository(SessionRepository):
    def __init__(self, redis_client):
        self.redis_client = redis_client

    def add(self, session: SessionEntity) -> SessionEntity:
        logger.info(
            "Saving session session_id=%s user_id=%s",
            session.id.value,
            session.user_id.value,
        )
        key_session = f"session:{session.id.value}"
        key_user_sessions = f"user:{session.user_id.value}"

        try:
            pipe = self.redis_client.pipeline()
            pipe.multi()

            pipe.hset(
                key_session,
                mapping={
                    "user_id": session.user_id.value,
                    "device": session.device.value,
                    "created_at": session.created_at.value,
                },
            )

            pipe.sadd(key_user_sessions, session.id.value)

            pipe.execute()
        except RedisError as e:
            logger.exception(
                "Failed to save session session_id=%s user_id=%s",
                session.id.value,
                session.user_id.value,
            )
            raise SessionStorageError("Failed to save session") from e

        logger.info("Session saved successfully")
        return session

    def delete(self, id: ID, user_id: ID) -> None:
        logger.info(
            "Starting session deletion session_id=%s user_id=%s",
            id.value,
            user_id.value,
        )
        key_session = f"session:{id.value}"
        key_user_sessions = f"user:{user_id.value}"

        try:
            pipe = self.redis_client.pipeline()
            pipe.multi()

            pipe.delete(key_session)
            pipe.srem(key_user_sessions, id.value)

            results = pipe.execute()
        except RedisError as e:
            logger.exception(
                "Failed to delete session session_id=%s user_id=%s",
                id.value,
                user_id.value,
            )
            raise SessionStorageError("Failed to delete session") from e

        deleted = results[0]
        removed = results[1]

        if deleted == 0:
            logger.warning("Session already deleted or never be exist")

        if removed == 0:
            logger.warning("Session not in user set or never be exist")

        logger.info("Session deleted successfully")

    def get_by_id(self, id: ID) -> SessionEntity:
        logger.info("Fetching session session_id=%s", id.value)
        key_session = f"session:{id.value}"

        try:
            data = self.redis_client.hgetall(key_session)
        except RedisError as e:
            logger.error(
                "Failed fetching session session_id=%s",
                id.value,
            )
            raise SessionStorageError("Failed fetching session") from e

        if not data:
            logger.debug("Session not found session_id=%s", id.value)
            raise SessionDoesNotExist("Session not found")

        user_id = data[b"user_id"].decode()
        device = data[b"device"].decode()
        created_at = data[b"created_at"].decode()

        logger.info("Successfully reconstructed session session_id=%s", id.value)

        return SessionFactory.create(
            user_id=user_id, device=device, session_id=id.value, created_at=created_at
        )

    def get_by_user_id(self, user_id: ID) -> List[SessionEntity]:
        key_user_sessions = f"user:{user_id.value}"
        logger.info("Fetching user's sessions user_id=%s", user_id.value)

        try:
            session_ids_bytes = self.redis_client.smembers(key_user_sessions)
            session_ids = {sid.decode() for sid in session_ids_bytes}
        except RedisError as e:
            logger.error(
                "Failed fetching user's session list user_id=%s",
                user_id.value,
            )
            raise SessionStorageError("Failed fetching user sessions") from e

        if not session_ids:
            logger.debug("No sessions found for user_id=%s", user_id.value)
            return []

        sessions = []
        for sid in session_ids:
            logger.debug("Processing session_id=%s for user_id=%s", sid, user_id.value)
            try:
                session = self.get_by_id(ID(sid))
                sessions.append(session)
            except SessionDoesNotExist:
                logger.warning(
                    "Session is in user list but not in storage: session_id=%s user_id=%s",
                    sid,
                    user_id.value,
                )
                continue

        logger.info(
            "Completed fetching user sessions: user_id=%s total_sessions=%s",
            user_id.value,
            len(sessions),
        )
        return sessions
