from collections.abc import AsyncIterator
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from src.domain.entities.order import Order
from src.domain.value_objects.currency import Currency
from src.domain.value_objects.idempotency_key import IdempotencyKey
from src.domain.value_objects.instrument_id import InstrumentId
from src.domain.value_objects.money import Money
from src.domain.value_objects.order_side import OrderSide
from src.domain.value_objects.order_type import OrderType
from src.domain.value_objects.quantity import Quantity
from src.domain.value_objects.time_in_force import TimeInForce
from src.domain.value_objects.trader_id import TraderId
from src.infrastructure.persistence.models import Base
from src.infrastructure.persistence.repositories.sqlalchemy_order_repository import (
    SQLAlchemyOrderRepository,
)

DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def session() -> AsyncIterator[AsyncSession]:
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as db_session:
        yield db_session
        await db_session.rollback()

    await engine.dispose()


@pytest_asyncio.fixture
async def repository(session: AsyncSession) -> SQLAlchemyOrderRepository:
    return SQLAlchemyOrderRepository(session)


@pytest.fixture
def trader_id() -> TraderId:
    return TraderId.generate()


@pytest.fixture
def instrument_id() -> InstrumentId:
    return InstrumentId.generate()


@pytest.fixture
def limit_order(trader_id: TraderId, instrument_id: InstrumentId) -> Order:
    order = Order.create(
        trader_id=trader_id,
        instrument_id=instrument_id,
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        time_in_force=TimeInForce.GTC,
        quantity=Quantity(100),
        idempotency_key=IdempotencyKey("infra-limit-001"),
        limit_price=Money(Decimal("10.50"), Currency.USD),
    )
    order.clear_changes()
    return order


@pytest.fixture
def market_order(trader_id: TraderId, instrument_id: InstrumentId) -> Order:
    order = Order.create(
        trader_id=trader_id,
        instrument_id=instrument_id,
        side=OrderSide.SELL,
        order_type=OrderType.MARKET,
        time_in_force=TimeInForce.IOC,
        quantity=Quantity(50),
        idempotency_key=IdempotencyKey("infra-market-001"),
    )
    order.clear_changes()
    return order
