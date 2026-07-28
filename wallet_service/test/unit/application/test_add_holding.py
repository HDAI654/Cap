from decimal import Decimal
from unittest.mock import AsyncMock
import pytest
from src.application.add_holding import AddHoldingCommand, AddHoldingHandler
from src.domain.entities.wallet import Wallet
from src.domain.value_objects.instrument_id import InstrumentId
from src.domain.value_objects.wallet_id import WalletId
from src.exceptions import InvalidCurrencyError


async def test_adds_holding(
    mock_uow: AsyncMock,
    mock_wallet_repository: AsyncMock,
    active_wallet: Wallet,
    sample_wallet_id: WalletId,
) -> None:
    instrument_id = InstrumentId.generate()
    mock_wallet_repository.get_by_id.return_value = active_wallet

    handler = AddHoldingHandler(mock_uow)
    await handler.handle(
        AddHoldingCommand(
            wallet_id=sample_wallet_id.value,
            instrument_id=instrument_id.value,
            quantity=10,
            average_cost=Decimal("25.50"),
            average_cost_currency="USD",
        )
    )

    holdings = active_wallet.holdings
    assert len(holdings) == 1
    assert holdings[0].instrument_id == instrument_id
    assert holdings[0].available.value == 10
    mock_wallet_repository.update.assert_awaited_once_with(active_wallet)
    mock_uow.commit.assert_awaited_once()


async def test_rejects_unsupported_currency(
    mock_uow: AsyncMock,
    mock_wallet_repository: AsyncMock,
    sample_wallet_id: WalletId,
) -> None:
    handler = AddHoldingHandler(mock_uow)

    with pytest.raises(InvalidCurrencyError):
        await handler.handle(
            AddHoldingCommand(
                wallet_id=sample_wallet_id.value,
                instrument_id=InstrumentId.generate().value,
                quantity=5,
                average_cost=Decimal("10.00"),
                average_cost_currency="XYZ",
            )
        )

    mock_wallet_repository.get_by_id.assert_not_awaited()
