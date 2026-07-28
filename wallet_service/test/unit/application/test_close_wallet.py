from unittest.mock import AsyncMock
from src.application.close_wallet import CloseWalletCommand, CloseWalletHandler
from src.domain.entities.wallet import Wallet
from src.domain.value_objects.wallet_id import WalletId
from src.domain.value_objects.wallet_status import WalletStatus


async def test_closes_active_wallet(
    mock_uow: AsyncMock,
    mock_wallet_repository: AsyncMock,
    active_wallet: Wallet,
    sample_wallet_id: WalletId,
) -> None:
    mock_wallet_repository.get_by_id.return_value = active_wallet

    handler = CloseWalletHandler(mock_uow)
    await handler.handle(CloseWalletCommand(wallet_id=sample_wallet_id.value))

    assert active_wallet.status == WalletStatus.CLOSED
    mock_wallet_repository.update.assert_awaited_once_with(active_wallet)
    mock_uow.commit.assert_awaited_once()


async def test_skips_persist_when_already_closed(
    mock_uow: AsyncMock,
    mock_wallet_repository: AsyncMock,
    closed_wallet: Wallet,
    sample_wallet_id: WalletId,
) -> None:
    mock_wallet_repository.get_by_id.return_value = closed_wallet

    handler = CloseWalletHandler(mock_uow)
    await handler.handle(CloseWalletCommand(wallet_id=sample_wallet_id.value))

    mock_wallet_repository.update.assert_not_awaited()
    mock_uow.commit.assert_not_awaited()
