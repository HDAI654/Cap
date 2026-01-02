from auth_app.domain.value_objects.id import ID
from auth_app.domain.value_objects.username import Username
from auth_app.domain.value_objects.email import Email
from auth_app.domain.value_objects.password import Password


class UserEntity:
    def __init__(
        self, username: Username, email: Email, password: Password, id: ID = None
    ):
        self.id = id or ID()
        self.username = username
        self.email = email
        self.password = password

    def __str__(self):
        return f"UserEntity(id={self.id}, username='{self.username}')"

    def __repr__(self):
        return f"UserEntity(id={self.id}, username='{self.username}')"

    def __eq__(self, other):
        return isinstance(other, UserEntity) and self.id == other.id

    def __hash__(self):
        return hash(self.id)
