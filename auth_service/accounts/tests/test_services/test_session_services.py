import pytest
import fakeredis
from ...services.session_service import SessionManager


@pytest.fixture(autouse=True)
def fake_redis(mocker):
    """Provides a patched redis_client inside SessionManager."""
    fake = fakeredis.FakeStrictRedis()
    mocker.patch(
        "auth.accounts.services.session_service.redis_client",
        fake,
    )
    return fake


@pytest.fixture
def user_id():
    return 42


@pytest.fixture
def device():
    return "test-device"


@pytest.mark.django_db
def test_new_session_creation(user_id, device):
    session = SessionManager.new_session(user_id, device)
    assert session.id is not None
    assert session.user_id == user_id
    assert session.device == device


@pytest.mark.django_db
def test_save_session_creates_redis_keys(fake_redis, user_id, device):
    session = SessionManager.new_session(user_id, device)
    session.save()

    # Check session hash
    key_session = f"session:{session.id}"
    assert fake_redis.exists(key_session)
    data = fake_redis.hgetall(key_session)
    assert data[b"user_id"].decode() == str(user_id)
    assert data[b"device"].decode() == device

    # Check user session list
    key_user_sessions = f"user:{user_id}"
    session_ids = fake_redis.lrange(key_user_sessions, 0, -1)
    assert session.id.encode() in session_ids


@pytest.mark.django_db
def test_delete_session_removes_redis_keys(fake_redis, user_id, device):
    session = SessionManager.new_session(user_id, device)
    session.save()

    session.delete()

    key_session = f"session:{session.id}"
    key_user_sessions = f"user:{user_id}"

    assert not fake_redis.exists(key_session)
    assert session.id.encode() not in fake_redis.lrange(key_user_sessions, 0, -1)


@pytest.mark.django_db
def test_get_session_returns_correct_session(user_id, device):
    session = SessionManager.new_session(user_id, device)
    session.save()

    fetched = SessionManager.get_session(session.id)
    assert fetched is not None
    assert fetched.id == session.id
    assert fetched.user_id == session.user_id
    assert fetched.device == session.device


@pytest.mark.django_db
def test_get_session_returns_none_if_missing():
    fetched = SessionManager.get_session("nonexistent")
    assert fetched is None


@pytest.mark.django_db
def test_get_user_sessions_returns_all_sessions(user_id, device):
    sessions = [SessionManager.new_session(user_id, device) for _ in range(3)]
    for s in sessions:
        s.save()

    user_sessions = SessionManager.get_user_sessions(user_id)
    assert len(user_sessions) == 3
    session_ids = [s.id for s in sessions]
    fetched_ids = [s.id for s in user_sessions]
    for sid in session_ids:
        assert sid in fetched_ids


@pytest.mark.django_db
def test_get_user_sessions_returns_empty_if_none():
    user_sessions = SessionManager.get_user_sessions(9999)
    assert user_sessions == []
