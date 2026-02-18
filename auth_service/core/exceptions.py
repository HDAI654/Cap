########### Basic Exceptions ###########
class AuthenticationFailed(Exception):
    """Raised when authentication fails due to invalid credentials (401)."""

    pass


class BadRequestError(Exception):
    """Base exception for client-side bad request errors (400)."""

    pass


########### User Exceptions ###########
class UserAlreadyExists(Exception):
    """Raised when trying to create a user that already exists."""

    pass


class UserNotFound(Exception):
    """Raised when trying to get a user that already doesn't exists."""

    pass


########### Token Exceptions ###########
class TokenCreationError(Exception):
    """Raised when token generation fails due to invalid input or system error."""

    pass


class InvalidToken(Exception):
    """Raised when the token is invalid."""

    pass


########### Session Exceptions ###########
class SessionDoesNotExist(Exception):
    """Raised when the session does not exist."""

    pass


class SessionStorageError(Exception):
    """Failed to read/write/delete session in cache."""

    pass


########### Utils Exceptions ###########
class IDGenerationError(Exception):
    """Raised when the IDGenerator.generate() had error"""

    pass


class ResponseProducerError(Exception):
    """Raised when the ResponseProducerError.build_response_with_tokens() had error"""

    pass


class PasswordHasherError(Exception):
    """Raised when the PasswordHasher.hash() or PasswordHasher.verify() had error"""

    pass
