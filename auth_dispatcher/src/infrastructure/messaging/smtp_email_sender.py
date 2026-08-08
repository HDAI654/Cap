import asyncio
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from src.conf import Config
from src.domain.ports.email_sender import EmailSender
from src.exceptions import EmailSendError

logger = logging.getLogger(__name__)


class SmtpEmailSender(EmailSender):
    """Send mail via SMTP."""

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        username: str | None = None,
        password: str | None = None,
        from_addr: str | None = None,
        use_tls: bool | None = None,
    ) -> None:
        self._host = host or Config.SMTP_HOST
        self._port = port if port is not None else Config.SMTP_PORT
        self._username = username if username is not None else Config.SMTP_USER
        self._password = password if password is not None else Config.SMTP_PASSWORD
        self._from = from_addr or Config.SMTP_FROM
        self._use_tls = Config.SMTP_USE_TLS if use_tls is None else use_tls

    async def send(
        self,
        *,
        to: str,
        subject: str,
        body: str,
        html: str | None = None,
    ) -> None:
        await asyncio.to_thread(
            self._send_sync, to=to, subject=subject, body=body, html=html
        )

    def _send_sync(
        self,
        *,
        to: str,
        subject: str,
        body: str,
        html: str | None,
    ) -> None:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self._from
        msg["To"] = to
        msg.attach(MIMEText(body, "plain", "utf-8"))
        if html:
            msg.attach(MIMEText(html, "html", "utf-8"))

        try:
            with smtplib.SMTP(self._host, self._port, timeout=30) as smtp:
                if self._use_tls:
                    smtp.starttls()
                if self._username:
                    smtp.login(self._username, self._password)
                smtp.sendmail(self._from, [to], msg.as_string())
            logger.info("Email sent to=%s subject=%s", to, subject)
        except OSError as exc:
            logger.exception("SMTP failure to=%s", to)
            raise EmailSendError(f"Failed to send email: {exc}") from exc
