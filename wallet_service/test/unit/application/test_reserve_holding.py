from decimal import Decimal
from unittest.mock import AsyncMock
from src.application.reserve_holding import (
    ReserveHoldingCommand,
    ReserveHoldingHandler,
)
from src.domain.entities.wallet import Wallet
from src.domain.value_objects.currency import Currency
from src.domain.value_objects.instrument_id import InstrumentId
from src.domain.value_objects.money import Money
from src.domain.value_objects.quantity import Quantity
from src.domain.value_objects.wallet_id import WalletId


async def test_reserves_holding(
    mock_uow: AsyncMock,
    mock_wallet_repository: AsyncMock,
    active_wallet: Wallet,
    sample_wallet_id: WalletId,
) -> None:
    instrument_id = InstrumentId.generate()
    active_wallet.add_holding(
        instrument_id,
        Quantity(20),
        Money(Decimal("15.00"), Currency.USD),
    )
    active_wallet.clear_changes()
    mock_wallet_repository.get_by_id.return_value = active_wallet

    handler = ReserveHoldingHandler(mock_uow)
    await handler.handle(
        ReserveHoldingCommand(
            wallet_id=sample_wallet_id.value,
            instrument_id=instrument_id.value,
            quantity=8,
        )
    )

    holding = active_wallet.holdings[0]
    assert holding.available.value == 12
    assert holding.reserved.value == 8
    mock_wallet_repository.update.assert_awaited_once_with(active_wallet)
    mock_uow.commit.assert_awaited_once()
