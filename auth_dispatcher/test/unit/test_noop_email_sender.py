import pytest

from src.infrastructure.messaging.noop_email_sender import NoOpEmailSender


@pytest.mark.asyncio
async def test_noop_does_not_raise() -> None:
    await NoOpEmailSender().send(
        to="a@b.com", subject="Hi", body="body", html="<p>x</p>"
    )
