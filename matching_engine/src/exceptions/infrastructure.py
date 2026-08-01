class InfrastructureError(Exception):
    """Base infrastructure error."""

    pass


class MessagingError(InfrastructureError):
    pass


class MessagingConnectionError(MessagingError):
    pass


class MessagingPublishError(MessagingError):
    pass


class MessagingConsumeError(MessagingError):
    pass


class CacheError(InfrastructureError):
    pass


class CacheConnectionError(CacheError):
    pass


class CacheOperationError(CacheError):
    pass
