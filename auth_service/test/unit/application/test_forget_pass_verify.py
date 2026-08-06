from unittest.mock import AsyncMock

import pytest

from src.application.forget_password import ForgetPasswordCommand, ForgetPasswordHandler
from src.domain.events.verification_token_created import VerificationTokenCreated


@pytest.mark.asyncio
async def test_forget_password_unknown_email_noop(
    mock_uow, mock_token_repo, mock_events
):
    mock_uow.users.exists_by_email = AsyncMock(return_value=False)
    handler = ForgetPasswordHandler(mock_uow, mock_token_repo, mock_events)
    await handler.handle(ForgetPasswordCommand(email="missing@x.com"))
    mock_token_repo.add.assert_not_awaited()
    mock_events.publish.assert_not_awaited()


@pytest.mark.asyncio
async def test_forget_password_known_email_publishes_event(
    mock_uow, mock_token_repo, mock_events
):
    mock_uow.users.exists_by_email = AsyncMock(return_value=True)
    handler = ForgetPasswordHandler(mock_uow, mock_token_repo, mock_events)
    await handler.handle(ForgetPasswordCommand(email="a@b.com"))
    mock_token_repo.add.assert_awaited_once()
    mock_events.publish.assert_awaited_once()
    event = mock_events.publish.await_args.args[0]
    assert isinstance(event, VerificationTokenCreated)
    assert event.token_type == "forget_pass_verify"
    assert event.email == "a@b.com"
