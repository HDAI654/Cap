from shared.entity import Entity
from src.domain.value_objects.email import Email
from src.domain.value_objects.hashed_password import HashedPassword
from src.domain.value_objects.role import Role
from src.domain.value_objects.user_id import UserId


class User(Entity):
    """Registered account with credentials and default role metadata."""

    def __init__(
        self,
        id: UserId,
        email: Email,
        hashed_password: HashedPassword,
        role: Role | None = None,
    ) -> None:
        self.id = id
        self.email = email
        self.hashed_password = hashed_password
        self.role = role if role is not None else Role.user()
        super().__init__()

    @classmethod
    def create(
        cls,
        email: str,
        hashed_password: str,
        *,
        id: str | None = None,
        role: str | None = None,
    ) -> "User":
        """Factory for a new user (defaults to USER role)."""
        return cls(
            id=UserId(id) if id is not None else UserId.generate(),
            email=Email(email),
            hashed_password=HashedPassword(hashed_password),
            role=Role(role) if role is not None else Role.user(),
        )

    def change_password(self, hashed_password: HashedPassword) -> None:
        """Replace stored password hash."""
        self.hashed_password = hashed_password
