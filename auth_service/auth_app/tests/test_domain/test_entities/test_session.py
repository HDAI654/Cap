from auth_app.domain.entities.session import SessionEntity
from auth_app.domain.value_objects.id import ID
from auth_app.domain.value_objects.device import Device
from auth_app.domain.value_objects.datetime import DateTime


class TestSession:
    def test_none_id(self):
        session = SessionEntity(
            user_id=ID(), device=Device("test-device"), created_at=DateTime()
        )

        assert session.id.value != None

    def test_eq_id(self):
        session = SessionEntity(
            id=ID("MyID"),
            user_id=ID(),
            device=Device("test-device"),
            created_at=DateTime(),
        )
        session2 = SessionEntity(
            id=ID("MyID"),
            user_id=ID(),
            device=Device("test-device"),
            created_at=DateTime(),
        )
        session3 = SessionEntity(
            user_id=ID(), device=Device("test-device"), created_at=DateTime()
        )

        assert session == session2
        assert session != session3 and session2 != session3
