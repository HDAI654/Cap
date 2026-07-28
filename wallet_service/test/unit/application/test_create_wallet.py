from unittest.mock import AsyncMock
import pytest
from src.application.create_wallet import (
    CreateWalletCommand,
    CreateWalletHandler,
    CreateWalletResult,
)
from src.domain.entities.wallet import Wallet
from src.domain.value_objects.trader_id import TraderId
from src.domain.value_objects.wallet_status import WalletStatus
from src.exceptions import WalletAlreadyExistsError


async def test_creates_wallet_when_trader_has_none(
    mock_uow: AsyncMock,
    mock_wallet_repository: AsyncMock,
    sample_trader_id: TraderId,
) -> None:
    mock_wallet_repository.exists_by_trader_id.return_value = False

    handler = CreateWalletHandler(mock_uow)
    result = await handler.handle(CreateWalletCommand(trader_id=sample_trader_id.value))

    assert isinstance(result, CreateWalletResult)
    assert result.wallet_id

    mock_wallet_repository.exists_by_trader_id.assert_awaited_once_with(
        sample_trader_id
    )
    mock_wallet_repository.add.assert_awaited_once()
    added: Wallet = mock_wallet_repository.add.await_args.args[0]
    assert added.trader_id == sample_trader_id
    assert added.status == WalletStatus.ACTIVE
    mock_uow.commit.assert_awaited_once()


async def test_raises_when_wallet_already_exists(
    mock_uow: AsyncMock,
    mock_wallet_repository: AsyncMock,
    sample_trader_id: TraderId,
) -> None:
    mock_wallet_repository.exists_by_trader_id.return_value = True

    handler = CreateWalletHandler(mock_uow)

    with pytest.raises(WalletAlreadyExistsError):
        await handler.handle(CreateWalletCommand(trader_id=sample_trader_id.value))

    mock_wallet_repository.add.assert_not_awaited()
    mock_uow.commit.assert_not_awaited()
