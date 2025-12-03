import unittest
from datetime import datetime, timedelta
from unittest.mock import patch
import fakeredis
from django.test import TestCase
from ...services.session_service import SessionManager


class SessionTests(TestCase):
    def setUp(self):
        self.fake_redis = fakeredis.FakeStrictRedis()

        # Patch the function INSIDE session_service
        patcher = patch(
            "auth.accounts.services.session_service.redis_client", self.fake_redis
        )
        self.mock_redis = patcher.start()
        self.addCleanup(patcher.stop)

        self.user_id = 42
        self.device = "test-device"

    def test_new_session_creation(self):
        session = SessionManager.new_session(self.user_id, self.device)
        self.assertIsNotNone(session.id)
        self.assertEqual(session.user_id, self.user_id)
        self.assertEqual(session.device, self.device)

    def test_save_session_creates_redis_keys(self):
        session = SessionManager.new_session(self.user_id, self.device)
        session.save()

        # Check session hash
        key_session = f"session:{session.id}"
        self.assertTrue(self.fake_redis.exists(key_session))
        data = self.fake_redis.hgetall(key_session)
        self.assertEqual(data[b"user_id"].decode(), str(self.user_id))
        self.assertEqual(data[b"device"].decode(), self.device)

        # Check user session list
        key_user_sessions = f"user:{self.user_id}"
        session_ids = self.fake_redis.lrange(key_user_sessions, 0, -1)
        self.assertIn(session.id.encode(), session_ids)

    def test_delete_session_removes_redis_keys(self):
        session = SessionManager.new_session(self.user_id, self.device)
        session.save()

        session.delete()

        key_session = f"session:{session.id}"
        key_user_sessions = f"user:{self.user_id}"

        self.assertFalse(self.fake_redis.exists(key_session))
        self.assertNotIn(
            session.id.encode(), self.fake_redis.lrange(key_user_sessions, 0, -1)
        )

    def test_revoke_session_regenerates_id_and_saves(self):
        session = SessionManager.new_session(self.user_id, self.device)
        session.save()
        old_id = session.id

        session.revoke()
        self.assertNotEqual(old_id, session.id)

        # Old session hash should be gone
        self.assertFalse(self.fake_redis.exists(f"session:{old_id}"))
        # New session hash should exist
        self.assertTrue(self.fake_redis.exists(f"session:{session.id}"))
        # User session list should contain new id
        key_user_sessions = f"user:{self.user_id}"
        self.assertIn(
            session.id.encode(), self.fake_redis.lrange(key_user_sessions, 0, -1)
        )
        self.assertNotIn(
            old_id.encode(), self.fake_redis.lrange(key_user_sessions, 0, -1)
        )

    def test_get_session_returns_correct_session(self):
        session = SessionManager.new_session(self.user_id, self.device)
        session.save()

        fetched = SessionManager.get_session(session.id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.id, session.id)
        self.assertEqual(fetched.user_id, session.user_id)
        self.assertEqual(fetched.device, session.device)

    def test_get_session_returns_none_if_missing(self):
        fetched = SessionManager.get_session("nonexistent")
        self.assertIsNone(fetched)

    def test_get_user_sessions_returns_all_sessions(self):
        sessions = [
            SessionManager.new_session(self.user_id, self.device) for _ in range(3)
        ]
        for s in sessions:
            s.save()

        user_sessions = SessionManager.get_user_sessions(self.user_id)
        self.assertEqual(len(user_sessions), 3)
        session_ids = [s.id for s in sessions]
        fetched_ids = [s.id for s in user_sessions]
        for sid in session_ids:
            self.assertIn(sid, fetched_ids)

    def test_get_user_sessions_returns_empty_if_none(self):
        user_sessions = SessionManager.get_user_sessions(9999)
        self.assertEqual(user_sessions, [])
