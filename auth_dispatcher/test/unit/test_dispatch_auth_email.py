"""Unit tests for DispatchAuthEmailHandler."""

from unittest.mock import AsyncMock

import pytest

from src.application.dispatch_auth_email import (
    EVENT_VERIFICATION_TOKEN_CREATED,
    DispatchAuthEmailHandler,
)


@pytest.mark.asyncio
async def test_verifyemail_sends_mail() -> None:
    sender = AsyncMock()
    handler = DispatchAuthEmailHandler(sender)
    await handler.handle(
        EVENT_VERIFICATION_TOKEN_CREATED,
        {
            "email": "a@b.com",
            "token": "11111111-1111-4111-8111-111111111111",
            "token_type": "verifyemail",
        },
    )
    sender.send.assert_awaited_once()
    kwargs = sender.send.await_args.kwargs
    assert kwargs["to"] == "a@b.com"
    assert "Verify" in kwargs["subject"]


@pytest.mark.asyncio
async def test_reset_sends_mail() -> None:
    sender = AsyncMock()
    handler = DispatchAuthEmailHandler(sender)
    await handler.handle(
        EVENT_VERIFICATION_TOKEN_CREATED,
        {
            "email": "a@b.com",
            "token": "11111111-1111-4111-8111-111111111111",
            "token_type": "forget_pass_verify",
        },
    )
    kwargs = sender.send.await_args.kwargs
    assert "Reset" in kwargs["subject"]


@pytest.mark.asyncio
async def test_missing_fields_skips() -> None:
    sender = AsyncMock()
    handler = DispatchAuthEmailHandler(sender)
    await handler.handle(EVENT_VERIFICATION_TOKEN_CREATED, {"email": "a@b.com"})
    sender.send.assert_not_awaited()


@pytest.mark.asyncio
async def test_unknown_event_ignored() -> None:
    sender = AsyncMock()
    handler = DispatchAuthEmailHandler(sender)
    await handler.handle("UserLoggedIn", {"email": "a@b.com"})
    sender.send.assert_not_awaited()
