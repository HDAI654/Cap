class ApplicationError(Exception):
    """Base application error."""

    pass


class OrderAlreadyExistsError(ApplicationError):
    """Raised when an order already exists for the given idempotency key."""

    pass


class InsufficientFundsError(ApplicationError):
    """Raised when wallet cannot reserve cash for a buy order."""

    pass


class InsufficientHoldingsError(ApplicationError):
    """Raised when wallet cannot reserve shares for a sell order."""

    pass


class InstrumentNotTradableError(ApplicationError):
    """Raised when the instrument is missing, halted, or not active."""

    pass


class WalletIntegrationError(ApplicationError):
    """Raised when the wallet service call fails unexpectedly."""

    pass
