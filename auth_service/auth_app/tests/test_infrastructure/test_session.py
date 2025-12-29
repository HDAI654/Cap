import pytest
from datetime import datetime, timezone
from unittest.mock import patch
import fakeredis
from redis.exceptions import RedisError
from auth_app.infrastructure.cache.session import Session, SessionManager
from auth_app.infrastructure.cache import session as session_file
from core.exceptions import SessionDoesNotExist, SessionStorageError


class TestSessionEntity:
    def test_session_creation_without_id_generates_random_id(self):
        session = Session(user_id=1, device="mobile")
        assert session.id is not None
        assert len(session.id) == 64  # 32 bytes hex = 64 chars
        assert session.user_id == 1
        assert session.device == "mobile"
        assert isinstance(session.created_at, datetime)
        assert session.created_at.tzinfo == timezone.utc

    def test_session_creation_with_id_preserves_id(self):
        session = Session(user_id=1, device="mobile", id="test123")
        assert session.id == "test123"
        assert session.user_id == 1
        assert session.device == "mobile"

    def test_session_creation_with_created_at(self):
        test_time = datetime(2023, 1, 1, tzinfo=timezone.utc)
        session = Session(user_id=1, device="mobile", created_at=test_time)
        assert session.created_at == test_time

    def test_session_equality_with_same_id(self):
        session1 = Session(user_id=1, device="mobile", id="same")
        session2 = Session(user_id=2, device="desktop", id="same")
        assert session1 == session2
        assert hash(session1) == hash(session2)

    def test_session_equality_with_different_id(self):
        session1 = Session(user_id=1, device="mobile", id="id1")
        session2 = Session(user_id=1, device="mobile", id="id2")
        assert session1 != session2
        assert hash(session1) != hash(session2)

    def test_session_equality_with_none_id(self):
        session1 = Session(user_id=1, device="mobile")
        session2 = Session(user_id=1, device="mobile")
        assert session1 != session2
        assert session1 is not session2

    def test_session_repr(self):
        session = Session(user_id=123, device="mobile", id="abc123")
        repr_str = repr(session)
        assert "Session" in repr_str
        assert "id=abc123" in repr_str
        assert "user_id=123" in repr_str
        assert "device='mobile'" in repr_str


class TestSessionManager:
    @pytest.fixture(autouse=True)
    def setup_redis(self):
        self.fake_redis = fakeredis.FakeRedis()

        patcher = patch(
            "auth_app.infrastructure.cache.session.redis_client", self.fake_redis
        )
        self.mock_redis = patcher.start()
        yield
        patcher.stop()

    def test_new_session_creates_session_without_id(self):
        session = SessionManager.new_session(user_id=1, device="mobile")
        assert session.user_id == 1
        assert session.device == "mobile"
        assert session.id is not None
        assert isinstance(session.created_at, datetime)

    def test_save_session_stores_data_in_redis(self):
        session = Session(user_id=1, device="mobile", id="session123")

        session.save()

        key_session = "session:session123"
        data = self.fake_redis.hgetall(key_session)
        assert data is not None
        assert data[b"user_id"] == b"1"
        assert data[b"device"] == b"mobile"
        assert b"created_at" in data

        key_user_sessions = "user:1"
        session_ids = self.fake_redis.smembers(key_user_sessions)
        assert b"session123" in session_ids

    def test_delete_session_removes_from_redis(self):
        session = Session(user_id=1, device="mobile", id="session123")
        session.save()

        session.delete()

        key_session = "session:session123"
        assert not self.fake_redis.exists(key_session)

        key_user_sessions = "user:1"
        session_ids = self.fake_redis.smembers(key_user_sessions)
        assert b"session123" not in session_ids

    def test_delete_nonexistent_session_warns_but_does_not_fail(self):
        session = Session(user_id=1, device="mobile", id="nonexistent")

        with patch.object(session_file, "logger") as mock_logger:
            session.delete()

            warning_calls = [
                call for call in mock_logger.method_calls if call[0] == "warning"
            ]
            assert len(warning_calls) >= 1

    def test_get_session_returns_session_from_redis(self):
        session_id = "test123"
        user_id = 456
        device = "desktop"
        created_at = datetime.now(timezone.utc).isoformat()

        self.fake_redis.hset(
            f"session:{session_id}",
            mapping={
                "user_id": str(user_id),
                "device": device,
                "created_at": created_at,
            },
        )

        session = SessionManager.get_session(session_id)

        assert session.id == session_id
        assert session.user_id == user_id
        assert session.device == device
        assert session.created_at.isoformat() == created_at

    def test_get_session_raises_when_not_found(self):
        with pytest.raises(SessionDoesNotExist, match="Session not found"):
            SessionManager.get_session("nonexistent")

    def test_get_session_raises_on_corrupted_data(self):
        session_id = "corrupted"
        self.fake_redis.hset(f"session:{session_id}", "user_id", "not_an_int")

        with pytest.raises(SessionStorageError, match="Invalid session data"):
            SessionManager.get_session(session_id)

    def test_get_session_raises_on_missing_fields(self):
        session_id = "incomplete"
        self.fake_redis.hset(f"session:{session_id}", "user_id", "123")
        # Missing device and created_at

        with pytest.raises(SessionStorageError, match="Invalid session data"):
            SessionManager.get_session(session_id)

    def test_get_user_sessions_returns_all_user_sessions(self):
        user_id = 789

        session1_id = "sess1"
        session2_id = "sess2"

        self.fake_redis.sadd(f"user:{user_id}", session1_id, session2_id)

        self.fake_redis.hset(
            f"session:{session1_id}",
            mapping={
                "user_id": str(user_id),
                "device": "mobile",
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        )

        self.fake_redis.hset(
            f"session:{session2_id}",
            mapping={
                "user_id": str(user_id),
                "device": "desktop",
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        )

        sessions = SessionManager.get_user_sessions(user_id)

        assert len(sessions) == 2
        session_ids = {s.id for s in sessions}
        assert session_ids == {session1_id, session2_id}

        for session in sessions:
            assert session.user_id == user_id
            assert session.device in ["mobile", "desktop"]

    def test_get_user_sessions_handles_orphaned_session_ids(self):
        user_id = 999
        good_id = "good_session"
        orphaned_id = "orphaned_session"

        self.fake_redis.sadd(f"user:{user_id}", good_id, orphaned_id)

        self.fake_redis.hset(
            f"session:{good_id}",
            mapping={
                "user_id": str(user_id),
                "device": "mobile",
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        # No hash for orphaned_id

        with patch.object(session_file, "logger") as mock_logger:
            sessions = SessionManager.get_user_sessions(user_id)

            warning_calls = [
                call for call in mock_logger.method_calls if call[0] == "warning"
            ]
            assert len(warning_calls) == 1

            assert len(sessions) == 1
            assert sessions[0].id == good_id

    def test_get_user_sessions_returns_empty_list_for_no_sessions(self):
        sessions = SessionManager.get_user_sessions(12345)
        assert sessions == []
        assert isinstance(sessions, list)

    def test_get_user_sessions_raises_on_redis_error(self):
        with patch.object(
            self.fake_redis, "smembers", side_effect=RedisError("Redis error")
        ):
            with pytest.raises(
                SessionStorageError, match="Failed fetching user sessions"
            ):
                SessionManager.get_user_sessions(1)

    def test_save_raises_on_redis_error(self):
        session = Session(user_id=1, device="mobile", id="test")

        with patch.object(
            self.fake_redis, "pipeline", side_effect=RedisError("Redis error")
        ):
            with pytest.raises(SessionStorageError, match="Failed to save session"):
                session.save()

    def test_delete_raises_on_redis_error(self):
        session = Session(user_id=1, device="mobile", id="test")

        with patch.object(
            self.fake_redis, "pipeline", side_effect=RedisError("Redis error")
        ):
            with pytest.raises(SessionStorageError, match="Failed to delete session"):
                session.delete()

    def test_atomic_save_and_delete_consistency(self):
        session = Session(user_id=1, device="mobile", id="atomic_test")

        session.save()

        assert self.fake_redis.exists(f"session:{session.id}")
        assert b"atomic_test" in self.fake_redis.smembers("user:1")

        session.delete()

        assert not self.fake_redis.exists(f"session:{session.id}")
        assert b"atomic_test" not in self.fake_redis.smembers("user:1")

    def test_save_is_idempotent(self):
        session = Session(user_id=1, device="mobile", id="idempotent")

        session.save()
        first_smembers = self.fake_redis.smembers("user:1")

        session.save()  # Second save should not create duplicates
        second_smembers = self.fake_redis.smembers("user:1")

        assert first_smembers == second_smembers
        assert len(second_smembers) == 1

    def test_delete_is_idempotent(self):
        session = Session(user_id=1, device="mobile", id="idempotent_del")

        session.save()
        session.delete()

        with patch.object(session_file, "logger") as mock_logger:
            session.delete()  # Second delete should not fail

            warning_calls = [
                call for call in mock_logger.method_calls if call[0] == "warning"
            ]
            assert len(warning_calls) >= 1
