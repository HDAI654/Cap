class ApplicationError(Exception):
    """Base application error."""

    pass


class InstrumentNotFoundError(ApplicationError):
    pass


class InstrumentAlreadyExistsError(ApplicationError):
    pass


class UnauthorizedError(ApplicationError):
    pass


class ForbiddenError(ApplicationError):
    pass
