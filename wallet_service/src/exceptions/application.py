class ApplicationError(Exception):
    """Base application error"""

    pass


class WalletAlreadyExistsError(ApplicationError):
    """Raised when a wallet already exists for the given trader."""

    pass
