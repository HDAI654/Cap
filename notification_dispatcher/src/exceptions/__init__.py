class InfrastructureError(Exception):
    """Base infrastructure error."""

    pass


class MessagingError(InfrastructureError):
    pass


class MessagingConnectionError(MessagingError):
    pass


class MessagingConsumeError(MessagingError):
    pass


class NotificationPushError(InfrastructureError):
    pass
