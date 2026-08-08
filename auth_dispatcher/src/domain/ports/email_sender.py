from abc import ABC, abstractmethod


class EmailSender(ABC):
    """Send a single email message."""

    @abstractmethod
    async def send(
        self,
        *,
        to: str,
        subject: str,
        body: str,
        html: str | None = None,
    ) -> None:
        raise NotImplementedError
