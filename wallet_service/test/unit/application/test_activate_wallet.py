import pytest
from src.application.activate_wallet import ActivateWalletCommand, ActivateWalletHandler
from src.domain.value_objects.wallet_status import WalletStatus
from src.exceptions import WalletNotFoundError


async def test_activate_wallet_success(mock_uow, locked_wallet):
    wallet_id = locked_wallet.id.value
    command = ActivateWalletCommand(wallet_id=wallet_id)

    mock_uow.wallets.get_by_id.return_value = locked_wallet

    handler = ActivateWalletHandler(uow=mock_uow)

    await handler.handle(command)

    assert locked_wallet.status == WalletStatus.ACTIVE
    mock_uow.wallets.update.assert_awaited_once_with(locked_wallet)
    mock_uow.commit.assert_awaited_once()


async def test_activate_wallet_already_active(mock_uow, active_wallet):
    wallet_id = active_wallet.id.value
    command = ActivateWalletCommand(wallet_id=wallet_id)

    mock_uow.wallets.get_by_id.return_value = active_wallet

    handler = ActivateWalletHandler(uow=mock_uow)

    # Act
    await handler.handle(command)

    # Assert
    # Status remains ACTIVE
    assert active_wallet.status == WalletStatus.ACTIVE

    # update and commit still called
    mock_uow.wallets.update.assert_awaited_once_with(active_wallet)
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_activate_wallet_not_found(mock_uow):
    """Handler propagates WalletNotFoundError if repository raises it."""
    wallet_id = "non-existent"
    command = ActivateWalletCommand(wallet_id=wallet_id)

    mock_uow.wallets.get_by_id.side_effect = WalletNotFoundError("Wallet not found")

    handler = ActivateWalletHandler(uow=mock_uow)

    # Act & Assert
    with pytest.raises(WalletNotFoundError):
        await handler.handle(command)

    # update and commit should NOT be called
    mock_uow.wallets.update.assert_not_awaited()
    mock_uow.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_activate_wallet_clear_changes_called(mock_uow, locked_wallet):
    """Ensure clear_changes is called after commit."""
    # Arrange
    wallet_id = locked_wallet.id.value
    command = ActivateWalletCommand(wallet_id=wallet_id)

    mock_uow.wallets.get_by_id.return_value = locked_wallet

    # Spy on clear_changes
    locked_wallet.clear_changes = MagicMock(wraps=locked_wallet.clear_changes)

    handler = ActivateWalletHandler(uow=mock_uow)

    # Act
    await handler.handle(command)

    # Assert
    locked_wallet.clear_changes.assert_called_once()
