"""No-op email sender for tests and local runs without SMTP."""

import logging

from src.domain.ports.email_sender import EmailSender

logger = logging.getLogger(__name__)


class NoOpEmailSender(EmailSender):
    async def send(
        self,
        *,
        to: str,
        subject: str,
        body: str,
        html: str | None = None,
    ) -> None:
        logger.info(
            "NoOpEmailSender to=%s subject=%s body_len=%d",
            to,
            subject,
            len(body),
        )
