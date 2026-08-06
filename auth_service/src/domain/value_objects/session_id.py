import uuid
from typing import Self
from shared.base_vo import BaseVO
from src.exceptions import InvalidSessionIdError


class SessionId(BaseVO[str]):
    """UUID v4 identifier for an auth session."""

    def __init__(self, value: str) -> None:
        if not isinstance(value, str):
            raise InvalidSessionIdError(
                f"SessionId must be string, got {type(value).__name__}"
            )
        value = value.strip()
        if not value:
            raise InvalidSessionIdError("SessionId must be a non-empty string")
        try:
            value = str(uuid.UUID(value, version=4))
        except Exception as exc:
            raise InvalidSessionIdError(f"Invalid UUID v4 format: {value}") from exc
        super().__init__(value)

    @classmethod
    def generate(cls) -> Self:
        """Generate a new session identifier."""
        return cls(str(uuid.uuid4()))
