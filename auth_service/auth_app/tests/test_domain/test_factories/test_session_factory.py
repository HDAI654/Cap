from datetime import datetime, timezone
from auth_app.domain.factories.session_factory import SessionFactory
from auth_app.domain.value_objects.id import ID
from auth_app.domain.value_objects.datetime import DateTime


class TestUserFactory:
    def test_create_success(self):
        session = SessionFactory.create(
            user_id="TestUserID",
            device="test-device",
            session_id="TestSessionID",
            created_at=1245542400.0,
        )

        dt = datetime(year=2009, month=6, day=21, tzinfo=timezone.utc).timestamp()

        assert session.id.value == "TestSessionID"
        assert session.user_id.value == "TestUserID"
        assert session.device.value == "test-device"
        assert session.created_at.value == dt

    def test_create_success_with_none_id(self):
        session = SessionFactory.create(
            user_id="TestUserID",
            device="test-device",
            created_at=1245542400.0,
        )

        dt = datetime(year=2009, month=6, day=21, tzinfo=timezone.utc).timestamp()

        assert isinstance(session.id, ID) and session.id.value
        assert session.user_id.value == "TestUserID"
        assert session.device.value == "test-device"
        assert session.created_at.value == dt

    def test_create_success_with_none_creatyed_at(self):
        session = SessionFactory.create(
            user_id="TestUserID",
            device="test-device",
            session_id="TestSessionID",
        )

        assert session.id.value == "TestSessionID"
        assert session.user_id.value == "TestUserID"
        assert session.device.value == "test-device"
        assert isinstance(session.created_at, DateTime) and session.created_at.value and isinstance(session.created_at.value, float)
