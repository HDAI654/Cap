class InfrastructureError(Exception):
    """Base infrastructure error."""

    pass


class CacheError(InfrastructureError):
    pass


class CacheConnectionError(CacheError):
    pass


class CacheOperationError(CacheError):
    pass
