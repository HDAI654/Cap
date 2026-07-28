from unittest.mock import AsyncMock
from src.application.activate_wallet import (
    ActivateWalletCommand,
    ActivateWalletHandler,
)
from src.domain.entities.wallet import Wallet
from src.domain.value_objects.wallet_id import WalletId
from src.domain.value_objects.wallet_status import WalletStatus


async def test_activates_locked_wallet(
    mock_uow: AsyncMock,
    mock_wallet_repository: AsyncMock,
    locked_wallet: Wallet,
    sample_wallet_id: WalletId,
) -> None:
    mock_wallet_repository.get_by_id.return_value = locked_wallet

    handler = ActivateWalletHandler(mock_uow)
    await handler.handle(ActivateWalletCommand(wallet_id=sample_wallet_id.value))

    assert locked_wallet.status == WalletStatus.ACTIVE
    mock_wallet_repository.update.assert_awaited_once_with(locked_wallet)
    mock_uow.commit.assert_awaited_once()


async def test_skips_persist_when_already_active(
    mock_uow: AsyncMock,
    mock_wallet_repository: AsyncMock,
    active_wallet: Wallet,
    sample_wallet_id: WalletId,
) -> None:
    mock_wallet_repository.get_by_id.return_value = active_wallet

    handler = ActivateWalletHandler(mock_uow)
    await handler.handle(ActivateWalletCommand(wallet_id=sample_wallet_id.value))

    mock_wallet_repository.update.assert_not_awaited()
    mock_uow.commit.assert_not_awaited()