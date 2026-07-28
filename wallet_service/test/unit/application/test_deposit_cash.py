from decimal import Decimal
from unittest.mock import AsyncMock
import pytest
from src.application.deposit_cash import DepositCashCommand, DepositCashHandler
from src.domain.entities.wallet import Wallet
from src.domain.value_objects.currency import Currency
from src.domain.value_objects.wallet_id import WalletId
from src.exceptions import InvalidCurrencyError


async def test_deposits_cash(
    mock_uow: AsyncMock,
    mock_wallet_repository: AsyncMock,
    active_wallet: Wallet,
    sample_wallet_id: WalletId,
) -> None:
    mock_wallet_repository.get_by_id.return_value = active_wallet
    amount = Decimal("100.00")

    handler = DepositCashHandler(mock_uow)
    await handler.handle(
        DepositCashCommand(
            wallet_id=sample_wallet_id.value,
            amount=amount,
            currency="USD",
        )
    )

    balances = active_wallet.cash_balances
    assert len(balances) == 1
    assert balances[0].currency == Currency.USD
    assert balances[0].available.amount == amount
    mock_wallet_repository.update.assert_awaited_once_with(active_wallet)
    mock_uow.commit.assert_awaited_once()


async def test_rejects_unsupported_currency(
    mock_uow: AsyncMock,
    mock_wallet_repository: AsyncMock,
    sample_wallet_id: WalletId,
) -> None:
    handler = DepositCashHandler(mock_uow)

    with pytest.raises(InvalidCurrencyError):
        await handler.handle(
            DepositCashCommand(
                wallet_id=sample_wallet_id.value,
                amount=Decimal("10.00"),
                currency="XYZ",
            )
        )

    mock_wallet_repository.get_by_id.assert_not_awaited()
    mock_uow.commit.assert_not_awaited()
