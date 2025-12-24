class AuthenticationFailed(Exception):
    """Raised when authentication fails due to invalid credentials."""
    pass

class UserAlreadyExists(Exception):
    """Raised when trying to create a user that already exists."""
    pass