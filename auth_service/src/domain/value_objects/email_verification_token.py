import uuid
from typing import Self
from shared.base_vo import BaseVO
from src.exceptions import InvalidEmailVerificationTokenError


class EmailVerificationToken(BaseVO[str]):
    """UUID v4 token stored in cache for verify-email and reset-password flows."""

    def __init__(self, value: str) -> None:
        if not isinstance(value, str):
            raise InvalidEmailVerificationTokenError(
                f"Token must be string, got {type(value).__name__}"
            )
        value = value.strip()
        if not value:
            raise InvalidEmailVerificationTokenError("Token must be non-empty")
        try:
            value = str(uuid.UUID(value, version=4))
        except Exception as exc:
            raise InvalidEmailVerificationTokenError(
                f"Invalid UUID v4 token: {value}"
            ) from exc
        super().__init__(value)

    @classmethod
    def generate(cls) -> Self:
        """Generate a fresh verification token."""
        return cls(str(uuid.uuid4()))
