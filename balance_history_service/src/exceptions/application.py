class ApplicationError(Exception):
    """Base application error."""

    pass


class TradeNotFoundError(ApplicationError):
    pass


class DuplicateTradeError(ApplicationError):
    pass
