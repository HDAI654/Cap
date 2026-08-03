from collections.abc import AsyncIterator
from datetime import datetime, timezone
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from src.domain.entities.order_history_entry import OrderHistoryEntry
from src.domain.entities.trade_record import TradeRecord
from src.infrastructure.persistence.models import Base
from src.infrastructure.persistence.repositories.sqlalchemy_order_history_repository import (
    SQLAlchemyOrderHistoryRepository,
)
from src.infrastructure.persistence.repositories.sqlalchemy_trade_repository import (
    SQLAlchemyTradeRepository,
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
async def session_factory() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    yield factory
    await engine.dispose()


@pytest_asyncio.fixture
async def trade_repository(session: AsyncSession) -> SQLAlchemyTradeRepository:
    return SQLAlchemyTradeRepository(session)


@pytest_asyncio.fixture
async def order_history_repository(
    session: AsyncSession,
) -> SQLAlchemyOrderHistoryRepository:
    return SQLAlchemyOrderHistoryRepository(session)


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


@pytest.fixture
def sample_order_entry() -> OrderHistoryEntry:
    return OrderHistoryEntry(
        entry_id="aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
        order_id="bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
        trader_id="cccccccc-cccc-4ccc-8ccc-cccccccccccc",
        instrument_id="dddddddd-dddd-4ddd-8ddd-dddddddddddd",
        event_type="OrderOpened",
        side="SELL",
        order_type="LIMIT",
        quantity=5,
        filled_quantity=0,
        remaining_quantity=5,
        price=Decimal("12.00"),
        price_currency="USD",
        status="OPEN",
        occurred_at=datetime.now(timezone.utc),
    )
