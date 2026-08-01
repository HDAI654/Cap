from shared.base_vo import BaseVO
from src.exceptions import InvalidIdempotencyKeyError


class IdempotencyKey(BaseVO[str]):
    """Client-supplied key that guarantees at-most-once order submission.

    Constraints:
        - Non-empty after stripping whitespace
        - Maximum length of 128 characters
    """

    MAX_LENGTH = 128

    def __init__(self, value: str) -> None:
        if not isinstance(value, str):
            raise InvalidIdempotencyKeyError(
                f"Idempotency key must be string, got {type(value).__name__}"
            )

        normalized = value.strip()
        if not normalized:
            raise InvalidIdempotencyKeyError(
                "Idempotency key must be a non-empty string"
            )

        if len(normalized) > self.MAX_LENGTH:
            raise InvalidIdempotencyKeyError(
                f"Idempotency key must be at most {self.MAX_LENGTH} characters"
            )

        super().__init__(normalized)
