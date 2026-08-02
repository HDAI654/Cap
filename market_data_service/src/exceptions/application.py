class ApplicationError(Exception):
    """Base application error."""

    pass


class MarketDataNotFoundError(ApplicationError):
    pass
