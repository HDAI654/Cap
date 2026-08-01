from unittest.mock import AsyncMock

import pytest

from src.domain.entities.order import Order
from src.domain.ports.order_repository import OrderRepository
from src.domain.ports.unit_of_work import UnitOfWork
from src.domain.value_objects.currency import Currency
from src.domain.value_objects.idempotency_key import IdempotencyKey
from src.domain.value_objects.instrument_id import InstrumentId
from src.domain.value_objects.money import Money
from src.domain.value_objects.order_side import OrderSide
from src.domain.value_objects.order_type import OrderType
from src.domain.value_objects.quantity import Quantity
from src.domain.value_objects.time_in_force import TimeInForce
from src.domain.value_objects.trader_id import TraderId

# ---------------------------------------------------------------------------
# Repository & Unit of Work
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_order_repository() -> AsyncMock:
    repo = AsyncMock(spec=OrderRepository)
    repo.add = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.get_by_idempotency_key = AsyncMock()
    repo.update = AsyncMock()
    repo.list_by_trader = AsyncMock()
    return repo


@pytest.fixture
def mock_uow(mock_order_repository: AsyncMock) -> AsyncMock:
    uow = AsyncMock(spec=UnitOfWork)
    uow.orders = mock_order_repository
    uow.commit = AsyncMock()
    uow.rollback = AsyncMock()
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=None)
    return uow


# ---------------------------------------------------------------------------
# Identifiers
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_trader_id() -> TraderId:
    return TraderId.generate()


@pytest.fixture
def sample_instrument_id() -> InstrumentId:
    return InstrumentId.generate()


# ---------------------------------------------------------------------------
# Real order aggregates
# ---------------------------------------------------------------------------


@pytest.fixture
def new_limit_order(
    sample_trader_id: TraderId,
    sample_instrument_id: InstrumentId,
) -> Order:
    order = Order.create(
        trader_id=sample_trader_id,
        instrument_id=sample_instrument_id,
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        time_in_force=TimeInForce.GTC,
        quantity=Quantity(100),
        idempotency_key=IdempotencyKey("limit-key-001"),
        limit_price=Money("10.50", Currency.USD),
    )
    order.clear_changes()
    return order


@pytest.fixture
def new_market_order(
    sample_trader_id: TraderId,
    sample_instrument_id: InstrumentId,
) -> Order:
    order = Order.create(
        trader_id=sample_trader_id,
        instrument_id=sample_instrument_id,
        side=OrderSide.SELL,
        order_type=OrderType.MARKET,
        time_in_force=TimeInForce.IOC,
        quantity=Quantity(50),
        idempotency_key=IdempotencyKey("market-key-001"),
    )
    order.clear_changes()
    return order


@pytest.fixture
def open_order(new_limit_order: Order) -> Order:
    new_limit_order.open()
    new_limit_order.clear_changes()
    return new_limit_order


@pytest.fixture
def partially_filled_order(open_order: Order) -> Order:
    open_order.fill(Quantity(40))
    open_order.clear_changes()
    return open_order


@pytest.fixture
def filled_order(open_order: Order) -> Order:
    open_order.fill(Quantity(100))
    open_order.clear_changes()
    return open_order
