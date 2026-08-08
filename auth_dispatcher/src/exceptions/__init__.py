"""Auth Dispatcher exceptions."""


class MessagingError(Exception):
    """RabbitMQ / messaging failure."""


class MessagingConnectionError(MessagingError):
    """Failed to connect to the bus."""


class EmailSendError(Exception):
    """Failed to send email."""
