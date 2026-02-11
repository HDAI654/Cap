from typing import Optional

class BaseAppException(Exception):
    """Base exception for all application errors"""
    def __init__(
        self,
        message: str,
        status_code: int,
        user_message: Optional[str] = None
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.user_message = user_message if user_message else message

    def __str__(self):
        return self.message
    
class AuthenticationFailed(Exception):
    """Raised when authentication fails due to invalid credentials."""

    pass

class UserAlreadyExists(Exception):
    """Raised when trying to create a user that already exists."""

    pass

class UserNotFound(Exception):
    """Raised when trying to get a user that already doesn't exists."""

    pass

class InvalidTokenError(Exception):
    """Raised when the token is invalid."""

    pass

class SessionDoesNotExist(Exception):
    """Raised when the session does not exist."""

    pass

class NoSessionFound(Exception):
    """Raised when the no session found."""

    pass

class InfrastructureError(Exception):
    """Base class for infrastructure failures."""

class CacheError(InfrastructureError):
    """Redis / cache failure."""

class SessionStorageError(CacheError):
    """Failed to read/write/delete session in cache."""
