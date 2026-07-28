from decimal import Decimal
from unittest.mock import AsyncMock
from src.application.DTOs import WalletDTO
from src.application.get_wallet import GetWalletHandler, GetWalletQuery
from src.domain.entities.wallet import Wallet
from src.domain.value_objects.currency import Currency
from src.domain.value_objects.instrument_id import InstrumentId
from src.domain.value_objects.money import Money
from src.domain.value_objects.quantity import Quantity
from src.domain.value_objects.wallet_id import WalletId
from src.domain.value_objects.wallet_status import WalletStatus


async def test_returns_wallet_dto(
    mock_uow: AsyncMock,
    mock_wallet_repository: AsyncMock,
    active_wallet: Wallet,
    sample_wallet_id: WalletId,
) -> None:
    instrument_id = InstrumentId.generate()
    active_wallet.deposit_cash(Money(Decimal("100.00"), Currency.USD))
    active_wallet.add_holding(
        instrument_id,
        Quantity(5),
        Money(Decimal("20.00"), Currency.USD),
    )
    mock_wallet_repository.get_by_id.return_value = active_wallet

    handler = GetWalletHandler(mock_uow)
    result = await handler.handle(GetWalletQuery(wallet_id=sample_wallet_id.value))

    assert isinstance(result, WalletDTO)
    assert result.wallet_id == sample_wallet_id.value
    assert result.trader_id == active_wallet.trader_id.value
    assert result.status == WalletStatus.ACTIVE.value
    assert len(result.cash_balances) == 1
    assert result.cash_balances[0].currency == "USD"
    assert result.cash_balances[0].available == Decimal("100.00")
    assert len(result.holdings) == 1
    assert result.holdings[0].instrument_id == instrument_id.value
    assert result.holdings[0].available == 5
    mock_uow.commit.assert_not_awaited()
