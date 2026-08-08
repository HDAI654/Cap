import logging
from typing import Any

from src.conf import Config
from src.domain.ports.email_sender import EmailSender

logger = logging.getLogger(__name__)

EVENT_VERIFICATION_TOKEN_CREATED = "VerificationTokenCreated"

TOKEN_TYPE_VERIFY = "verifyemail"
TOKEN_TYPE_RESET = "forget_pass_verify"


class DispatchAuthEmailHandler:
    """Consume auth events and send the corresponding email."""

    def __init__(self, email_sender: EmailSender) -> None:
        self._email = email_sender

    async def handle(self, event_type: str, payload: dict[str, Any]) -> None:
        if event_type != EVENT_VERIFICATION_TOKEN_CREATED:
            logger.debug("Ignoring unsupported event_type=%s", event_type)
            return

        email = str(payload.get("email") or "").strip()
        token = str(payload.get("token") or "").strip()
        token_type = str(payload.get("token_type") or TOKEN_TYPE_VERIFY).strip()

        if not email or not token:
            logger.warning("VerificationTokenCreated missing email/token — skip")
            return

        if token_type == TOKEN_TYPE_RESET:
            subject, body, html = self._reset_templates(token)
        else:
            subject, body, html = self._verify_templates(token)

        await self._email.send(to=email, subject=subject, body=body, html=html)
        logger.info(
            "Auth email dispatched type=%s to=%s",
            token_type,
            email,
        )

    def _verify_templates(self, token: str) -> tuple[str, str, str]:
        link = f"{Config.VERIFY_EMAIL_URL}/{token}"
        name = Config.APP_DISPLAY_NAME
        subject = f"Verify Your Email Address — {name}"
        body = (
            f"Welcome to {name}!\n\n"
            f"Verify your email:\n{link}\n\n"
            f"Support: {Config.SUPPORT_EMAIL}\n"
        )
        html = (
            f"<p>Welcome to <strong>{name}</strong>!</p>"
            f'<p><a href="{link}">Verify your email</a></p>'
            f"<p>Support: {Config.SUPPORT_EMAIL}</p>"
        )
        return subject, body, html

    def _reset_templates(self, token: str) -> tuple[str, str, str]:
        link = f"{Config.RESET_PASSWORD_URL}/{token}"
        name = Config.APP_DISPLAY_NAME
        subject = f"Reset Your Password — {name}"
        body = (
            f"Reset your {name} password:\n{link}\n\n"
            f"If you did not request this, ignore this email.\n"
            f"Support: {Config.SUPPORT_EMAIL}\n"
        )
        html = (
            f"<p>Reset your <strong>{name}</strong> password:</p>"
            f'<p><a href="{link}">Reset password</a></p>'
            f"<p>If you did not request this, ignore this email.</p>"
        )
        return subject, body, html
