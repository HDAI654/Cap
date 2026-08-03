from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from src.domain.entities.trade_record import TradeRecord
from src.domain.ports.order_history_repository import OrderHistoryRepository
from src.domain.ports.trade_repository import TradeRepository
from src.domain.ports.unit_of_work import UnitOfWork


@pytest.fixture
def mock_trade_repo() -> AsyncMock:
    repo = AsyncMock(spec=TradeRepository)
    repo.add = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.list_by_trader = AsyncMock()
    repo.list_by_instrument = AsyncMock()
    repo.exists = AsyncMock(return_value=False)
    return repo


@pytest.fixture
def mock_order_history_repo() -> AsyncMock:
    repo = AsyncMock(spec=OrderHistoryRepository)
    repo.add = AsyncMock()
    repo.list_by_order = AsyncMock()
    repo.list_by_trader = AsyncMock()
    return repo


@pytest.fixture
def mock_uow(
    mock_trade_repo: AsyncMock,
    mock_order_history_repo: AsyncMock,
) -> AsyncMock:
    uow = AsyncMock(spec=UnitOfWork)
    uow.trades = mock_trade_repo
    uow.order_history = mock_order_history_repo
    uow.commit = AsyncMock()
    uow.rollback = AsyncMock()
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=None)
    return uow


@pytest.fixture
def sample_trade() -> TradeRecord:
    return TradeRecord(
        trade_id="11111111-1111-4111-8111-111111111111",
        maker_order_id="22222222-2222-4222-8222-222222222222",
        taker_order_id="33333333-3333-4333-8333-333333333333",
        buyer_id="44444444-4444-4444-8444-444444444444",
        seller_id="55555555-5555-4555-8555-555555555555",
        instrument_id="66666666-6666-4666-8666-666666666666",
        quantity=10,
        execution_price=Decimal("100.50"),
        execution_price_currency="USD",
        sequence_number=1,
        executed_at=datetime.now(timezone.utc),
    )
