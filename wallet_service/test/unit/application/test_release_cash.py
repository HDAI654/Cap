from decimal import Decimal
from unittest.mock import AsyncMock
import pytest
from src.application.release_cash import ReleaseCashCommand, ReleaseCashHandler
from src.domain.entities.wallet import Wallet
from src.domain.value_objects.currency import Currency
from src.domain.value_objects.money import Money
from src.domain.value_objects.wallet_id import WalletId
from src.exceptions import InvalidCurrencyError


async def test_releases_reserved_cash(
    mock_uow: AsyncMock,
    mock_wallet_repository: AsyncMock,
    active_wallet: Wallet,
    sample_wallet_id: WalletId,
) -> None:
    active_wallet.deposit_cash(Money(Decimal("200.00"), Currency.USD))
    active_wallet.reserve_cash(Money(Decimal("80.00"), Currency.USD))
    active_wallet.clear_changes()
    mock_wallet_repository.get_by_id.return_value = active_wallet

    handler = ReleaseCashHandler(mock_uow)
    await handler.handle(
        ReleaseCashCommand(
            wallet_id=sample_wallet_id.value,
            amount=Decimal("30.00"),
            currency="USD",
        )
    )

    balance = active_wallet.cash_balances[0]
    assert balance.available.amount == Decimal("150.00")
    assert balance.reserved.amount == Decimal("50.00")
    mock_wallet_repository.update.assert_awaited_once_with(active_wallet)
    mock_uow.commit.assert_awaited_once()


async def test_rejects_unsupported_currency(
    mock_uow: AsyncMock,
    mock_wallet_repository: AsyncMock,
    sample_wallet_id: WalletId,
) -> None:
    handler = ReleaseCashHandler(mock_uow)

    with pytest.raises(InvalidCurrencyError):
        await handler.handle(
            ReleaseCashCommand(
                wallet_id=sample_wallet_id.value,
                amount=Decimal("10.00"),
                currency="XYZ",
            )
        )

    mock_wallet_repository.get_by_id.assert_not_awaited()
