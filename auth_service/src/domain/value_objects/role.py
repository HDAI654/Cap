from typing import Self
from shared.base_vo import BaseVO
from src.exceptions import InvalidRoleError

_ALLOWED = frozenset({"USER", "ADMIN"})


class Role(BaseVO[str]):
    """Token/session role claim (USER or ADMIN)."""

    def __init__(self, value: str) -> None:
        if not isinstance(value, str):
            raise InvalidRoleError(f"Role must be string, got {type(value).__name__}")
        normalized = value.strip().upper()
        if normalized not in _ALLOWED:
            raise InvalidRoleError(f"Invalid role: {value}")
        super().__init__(normalized)

    @classmethod
    def user(cls) -> Self:
        """Standard trader/user role."""
        return cls("USER")

    @classmethod
    def admin(cls) -> Self:
        """Elevated admin role."""
        return cls("ADMIN")

    @property
    def is_admin(self) -> bool:
        return self.value == "ADMIN"
