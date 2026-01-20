from auth_app.domain.value_objects.id import ID
from auth_app.domain.value_objects.datetime import DateTime
from auth_app.domain.value_objects.device import Device


class SessionEntity:
    def __init__(
        self,
        user_id: ID,
        device: Device,
        id: ID = None,
        created_at: DateTime = None,
    ):
        self.user_id = user_id
        self.device = device
        self.created_at = created_at or DateTime()
        self.id = id or ID()

    def __str__(self):
        return f"Session(id='{self.id}', user_id='{self.user_id}', device='{self.device}', created_at='{self.created_at}')"

    def __repr__(self):
        return f"Session(id='{self.id}', user_id='{self.user_id}', device='{self.device}', created_at='{self.created_at}')"

    def __eq__(self, other):
        return isinstance(other, SessionEntity) and self.id == other.id

    def __hash__(self):
        return hash((self.id,))
