import pytest
from datetime import datetime, timezone
from unittest.mock import patch
import fakeredis
from redis.exceptions import RedisError
from auth_app.infrastructure.cache.session_repository import RedisSessionRepository
from auth_app.infrastructure.cache import session_repository as session_repository_file
from auth_app.domain.factories.session_factory import SessionFactory
from auth_app.domain.value_objects.id import ID
from core.exceptions import SessionDoesNotExist, SessionStorageError
from time import sleep


class TestSessionManager:
    fake_redis = fakeredis.FakeRedis()
    repo = RedisSessionRepository(redis_client=fake_redis)

    @pytest.fixture()
    def session(self):
        return SessionFactory.create(
            user_id=ID().value, device="test-device", created_at=1245542400.0
        )

    @pytest.fixture()
    def user_id(self):
        return ID()

    def test_add_session(self, session):
        self.repo.add(session)

        key_session = f"session:{session.id.value}"
        data = self.fake_redis.hgetall(key_session)
        assert data is not None
        assert data[b"user_id"].decode() == session.user_id
        assert data[b"device"].decode() == session.device
        assert float(data[b"created_at"].decode()) == session.created_at

        key_user_sessions = f"user:{session.user_id.value}"
        session_ids = self.fake_redis.smembers(key_user_sessions)

        assert session.id.value.encode() in session_ids

    def test_delete_session(self, session):
        self.repo.add(session)

        key_session = f"session:{session.id.value}"

        self.repo.delete(id=session.id, user_id=session.user_id)

        assert not self.fake_redis.exists(key_session)

        key_user_sessions = "user:1"
        session_ids = self.fake_redis.smembers(key_user_sessions)

        assert session.id.value.encode() not in session_ids

    def test_delete_nonexistent_session_warns_but_does_not_fail(self, session):
        with patch.object(session_repository_file, "logger") as mock_logger:
            self.repo.delete(id=session.id, user_id=session.user_id)

            warning_calls = [
                call for call in mock_logger.method_calls if call[0] == "warning"
            ]
            assert len(warning_calls) >= 1

    def test_get_session_by_id(self, session):
        self.repo.add(session)

        session2 = self.repo.get_by_id(id=session.id)

        assert session.id == session2.id
        assert session.user_id == session2.user_id
        assert session.device == session2.device
        assert session.created_at == session2.created_at

    def test_get_session_raises_when_not_found(self):
        with pytest.raises(SessionDoesNotExist):
            self.repo.get_by_id(ID("nonexistent-session-id"))

    def test_get_sessions_by_user_id(self):
        user_id = "user-id"
        session1 = SessionFactory.create(
            user_id=user_id, device="test-device", created_at=1245542400.0
        )

        session2 = SessionFactory.create(
            user_id=user_id, device="test-device", created_at=1245542400.0
        )
        self.repo.add(session1)
        self.repo.add(session2)

        sessions = self.repo.get_by_user_id(user_id=ID(user_id))

        assert len(sessions) == 2
        session_ids = {s.id for s in sessions}
        assert session_ids == {session1.id, session2.id}

        for session in sessions:
            assert session.user_id == user_id

    def test_get_user_sessions_handles_orphaned_session_ids(self, user_id):
        user_id = user_id.value
        good_id = "good_session"
        orphaned_id = "orphaned_session"

        self.fake_redis.sadd(f"user:{user_id}", good_id, orphaned_id)

        self.fake_redis.hset(
            f"session:{good_id}",
            mapping={
                "user_id": user_id,
                "device": "mobile",
                "created_at": datetime.now(timezone.utc).timestamp(),
            },
        )

        with patch.object(session_repository_file, "logger") as mock_logger:
            sessions = self.repo.get_by_user_id(ID(user_id))

            warning_calls = [
                call for call in mock_logger.method_calls if call[0] == "warning"
            ]
            assert len(warning_calls) == 1

            assert len(sessions) == 1
            assert sessions[0].id == good_id

    def test_get_user_sessions_returns_empty_list_for_no_sessions(self, user_id):
        sessions = self.repo.get_by_user_id(user_id)
        assert isinstance(sessions, list)
        assert sessions == []

    def test_get_session_by_id_raises_on_redis_error(self):
        with patch.object(
            self.fake_redis, "hgetall", side_effect=RedisError("Redis error")
        ):
            with pytest.raises(SessionStorageError):
                self.repo.get_by_id(ID())

    def test_get_session_by_user_id_raises_on_redis_error(self, user_id):
        with patch.object(
            self.fake_redis, "smembers", side_effect=RedisError("Redis error")
        ):
            with pytest.raises(SessionStorageError):
                self.repo.get_by_user_id(user_id)

    def test_add_raises_on_redis_error(self, session):
        with patch.object(
            self.fake_redis, "pipeline", side_effect=RedisError("Redis error")
        ):
            with pytest.raises(SessionStorageError):
                self.repo.add(session)

    def test_delete_raises_on_redis_error(self, session):
        with patch.object(
            self.fake_redis, "pipeline", side_effect=RedisError("Redis error")
        ):
            with pytest.raises(SessionStorageError, match="Failed to delete session"):
                self.repo.delete(session.id, session.user_id)

    def test_atomic_add_and_delete_consistency(self, session):
        self.repo.add(session)

        assert self.fake_redis.exists(f"session:{session.id.value}")
        assert session.id.value.encode() in self.fake_redis.smembers(
            f"user:{session.user_id.value}"
        )

        self.repo.delete(session.id, session.user_id)

        assert not self.fake_redis.exists(f"session:{session.id.value}")
        assert session.id.value.encode() not in self.fake_redis.smembers(
            f"user:{session.user_id.value}"
        )

    def test_save_is_idempotent(self, session):
        self.repo.add(session)
        first_smembers = self.fake_redis.smembers(f"user:{session.user_id.value}")

        self.repo.add(session)  # Second save should not create duplicates
        second_smembers = self.fake_redis.smembers(f"user:{session.user_id.value}")

        assert first_smembers == second_smembers
        assert len(second_smembers) == 1

    def test_delete_all_user_sessions_deletes_all_sessions(self, user_id):
        """Test that all sessions for a user are deleted."""
        # Create multiple sessions for the same user
        session1 = SessionFactory.create(
            user_id=user_id.value, device="mobile", created_at=1245542400.0
        )
        session2 = SessionFactory.create(
            user_id=user_id.value, device="tablet", created_at=1245542400.0
        )
        session3 = SessionFactory.create(
            user_id=user_id.value, device="desktop", created_at=1245542400.0
        )

        self.repo.add(session1)
        self.repo.add(session2)
        self.repo.add(session3)

        # Verify sessions exist
        assert self.fake_redis.exists(f"session:{session1.id.value}")
        assert self.fake_redis.exists(f"session:{session2.id.value}")
        assert self.fake_redis.exists(f"session:{session3.id.value}")
        assert self.fake_redis.scard(f"user:{user_id.value}") == 3

        # Delete all sessions
        self.repo.delete_all_user_sessions(user_id)

        # Verify all sessions are deleted
        assert not self.fake_redis.exists(f"session:{session1.id.value}")
        assert not self.fake_redis.exists(f"session:{session2.id.value}")
        assert not self.fake_redis.exists(f"session:{session3.id.value}")
        assert not self.fake_redis.exists(f"user:{user_id.value}")

    def test_delete_all_user_sessions_with_no_sessions(self, user_id):
        """Test deleting all sessions when user has no sessions."""
        # Verify no sessions initially
        assert self.fake_redis.scard(f"user:{user_id.value}") == 0

        # Should not raise any exception
        self.repo.delete_all_user_sessions(user_id)

        # Verify still no sessions
        assert self.fake_redis.scard(f"user:{user_id.value}") == 0

    def test_delete_all_user_sessions_with_orphaned_sessions(self, user_id):
        """Test deleting all sessions when some sessions are missing."""
        # Create a session that exists
        good_session = SessionFactory.create(
            user_id=user_id.value, device="mobile", created_at=1245542400.0
        )
        self.repo.add(good_session)

        # Manually add orphaned session ID to user set
        orphaned_id = "orphaned-session-id"
        self.fake_redis.sadd(f"user:{user_id.value}", orphaned_id)

        # Verify state
        assert self.fake_redis.exists(f"session:{good_session.id.value}")
        assert not self.fake_redis.exists(f"session:{orphaned_id}")
        assert self.fake_redis.scard(f"user:{user_id.value}") == 2

        # Delete all sessions
        self.repo.delete_all_user_sessions(user_id)

        # Verify both session and orphaned ID are gone from user set
        assert not self.fake_redis.exists(f"user:{user_id.value}")

        # Verify good session is deleted
        assert not self.fake_redis.exists(f"session:{good_session.id.value}")

    def test_delete_all_user_sessions_raises_on_redis_error(self, user_id):
        """Test that SessionStorageError is raised on Redis error."""
        with patch.object(
            self.fake_redis, "smembers", side_effect=RedisError("Redis error")
        ):
            with pytest.raises(
                SessionStorageError, match="Failed to delete all user sessions"
            ):
                self.repo.delete_all_user_sessions(user_id)

    def test_delete_all_user_sessions_atomic_consistency(self, user_id):
        """Test that operation is atomic - all or nothing."""
        # Create sessions
        session1 = SessionFactory.create(
            user_id=user_id.value, device="mobile", created_at=1245542400.0
        )
        session2 = SessionFactory.create(
            user_id=user_id.value, device="tablet", created_at=1245542400.0
        )

        self.repo.add(session1)
        self.repo.add(session2)

        # Mock pipeline to fail after deleting some sessions
        original_pipeline = self.fake_redis.pipeline

        def failing_pipeline():
            pipe = original_pipeline()
            original_execute = pipe.execute

            def execute_with_failure():
                # First delete operations might succeed
                result = original_execute()
                # Then raise error
                raise RedisError("Simulated failure")

            pipe.execute = execute_with_failure
            return pipe

        with patch.object(self.fake_redis, "pipeline", side_effect=failing_pipeline):
            with pytest.raises(SessionStorageError):
                self.repo.delete_all_user_sessions(user_id)

    def test_delete_all_user_sessions_multiple_users_isolated(self):
        """Test that deleting sessions for one user doesn't affect another."""
        user1 = ID()
        user2 = ID()

        # Create sessions for both users
        session_user1 = SessionFactory.create(
            user_id=user1.value, device="mobile", created_at=1245542400.0
        )
        session_user2 = SessionFactory.create(
            user_id=user2.value, device="tablet", created_at=1245542400.0
        )

        self.repo.add(session_user1)
        self.repo.add(session_user2)

        # Delete only user1's sessions
        self.repo.delete_all_user_sessions(user1)

        # Verify user1's sessions are gone
        assert not self.fake_redis.exists(f"session:{session_user1.id.value}")
        assert not self.fake_redis.exists(f"user:{user1.value}")

        # Verify user2's sessions remain
        assert self.fake_redis.exists(f"session:{session_user2.id.value}")
        assert self.fake_redis.scard(f"user:{user2.value}") == 1
