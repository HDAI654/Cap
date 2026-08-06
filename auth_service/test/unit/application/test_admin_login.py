from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from src.application.admin_login import AdminLoginCommand, AdminLoginHandler
from src.domain.value_objects.role import Role
from src.exceptions import InvalidEmailOrPasswordError


@pytest.mark.asyncio
async def test_admin_login_requires_hash_config(
    mock_uow, mock_sessions, mock_encoder, mock_hasher, sample_user
):
    with patch("src.application.admin_login.Config") as cfg:
        cfg.ADMIN_PASSWORD_HASH = ""
        handler = AdminLoginHandler(mock_uow, mock_sessions, mock_encoder, mock_hasher)
        with pytest.raises(InvalidEmailOrPasswordError):
            await handler.handle(
                AdminLoginCommand(
                    email="trader@example.com",
                    password="secret1A",
                    admin_password="admin",
                    device="web",
                )
            )


@pytest.mark.asyncio
async def test_admin_login_success(
    mock_uow, mock_sessions, mock_encoder, mock_hasher, mock_events, sample_user
):
    mock_uow.users.get_by_email = AsyncMock(return_value=sample_user)
    with patch("src.application.admin_login.Config") as cfg:
        cfg.ADMIN_PASSWORD_HASH = "$2b$12$placeholder"
        with patch.object(
            AdminLoginHandler, "_verify_admin_password", return_value=True
        ):
            handler = AdminLoginHandler(
                mock_uow, mock_sessions, mock_encoder, mock_hasher, mock_events
            )
            result = await handler.handle(
                AdminLoginCommand(
                    email="trader@example.com",
                    password="secret1A",
                    admin_password="admin-secret",
                    device="web",
                )
            )
    assert result.access_token == "access.jwt"
    role_arg = mock_encoder.create_access_token.call_args.args[3]
    assert role_arg == Role.admin()
