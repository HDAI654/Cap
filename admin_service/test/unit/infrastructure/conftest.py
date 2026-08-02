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

from src.domain.entities.instrument import Instrument
from src.domain.value_objects.currency import Currency
from src.domain.value_objects.money import Money
from src.domain.value_objects.quantity import Quantity
from src.infrastructure.persistence.models import Base
from src.infrastructure.persistence.repositories.sqlalchemy_instrument_repository import (
    SQLAlchemyInstrumentRepository,
)
from src.infrastructure.persistence.unit_of_work import SQLAlchemyUnitOfWork

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
async def repository(session: AsyncSession) -> SQLAlchemyInstrumentRepository:
    return SQLAlchemyInstrumentRepository(session)


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


@pytest.fixture
def sample_instrument() -> Instrument:
    instrument = Instrument.create(
        symbol="AAPL",
        name="Apple Inc.",
        tick_size=Money(Decimal("0.01"), Currency.USD),
        lot_size=Quantity(1),
        minimum_order_quantity=Quantity(1),
        maximum_order_quantity=Quantity(10000),
        currency=Currency.USD,
        total_shares=Quantity(0),
    )
    instrument.clear_changes()
    return instrument


@pytest.fixture
def other_instrument() -> Instrument:
    instrument = Instrument.create(
        symbol="MSFT",
        name="Microsoft Corp.",
        tick_size=Money(Decimal("0.01"), Currency.USD),
        lot_size=Quantity(1),
        minimum_order_quantity=Quantity(1),
        maximum_order_quantity=Quantity(5000),
        currency=Currency.USD,
        total_shares=Quantity(100),
    )
    instrument.clear_changes()
    return instrument
