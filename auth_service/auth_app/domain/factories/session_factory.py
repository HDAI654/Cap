from auth_app.domain.entities.session import SessionEntity
from auth_app.domain.value_objects.id import ID
from auth_app.domain.value_objects.datetime import DateTime
from auth_app.domain.value_objects.device import Device


class SessionFactory:
    @staticmethod
    def create(
        *, user_id: str, device: str, session_id: str = None, created_at: float | int = None
    ) -> SessionEntity:
        """
        Create a new SessionEntity.
        """

        return SessionEntity(
            user_id=ID(user_id),
            device=Device(device),
            id=ID(session_id),
            created_at=DateTime(created_at),
        )
