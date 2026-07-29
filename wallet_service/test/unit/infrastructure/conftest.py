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
from src.domain.entities.wallet import Wallet
from src.domain.value_objects.currency import Currency
from src.domain.value_objects.instrument_id import InstrumentId
from src.domain.value_objects.money import Money
from src.domain.value_objects.quantity import Quantity
from src.domain.value_objects.trader_id import TraderId
from src.domain.value_objects.wallet_id import WalletId
from src.domain.value_objects.wallet_status import WalletStatus
from src.infrastructure.persistence.models import Base
from src.infrastructure.persistence.repositories.sqlalchemy_wallet_repository import (
    SQLAlchemyWalletRepository,
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
async def repository(session: AsyncSession) -> SQLAlchemyWalletRepository:
    return SQLAlchemyWalletRepository(session)


@pytest.fixture
def trader_id() -> TraderId:
    return TraderId.generate()


@pytest.fixture
def wallet_id() -> WalletId:
    return WalletId.generate()


@pytest.fixture
def instrument_id() -> InstrumentId:
    return InstrumentId.generate()


@pytest.fixture
def empty_wallet(wallet_id: WalletId, trader_id: TraderId) -> Wallet:
    wallet = Wallet(
        id=wallet_id,
        trader_id=trader_id,
        status=WalletStatus.ACTIVE,
    )
    wallet.clear_changes()
    return wallet


@pytest.fixture
def funded_wallet(
    wallet_id: WalletId,
    trader_id: TraderId,
    instrument_id: InstrumentId,
) -> Wallet:
    wallet = Wallet(
        id=wallet_id,
        trader_id=trader_id,
        status=WalletStatus.ACTIVE,
    )
    wallet.deposit_cash(Money(Decimal("100.00"), Currency.USD))
    wallet.add_holding(
        instrument_id,
        Quantity(10),
        Money(Decimal("25.50"), Currency.USD),
    )
    wallet.clear_changes()
    return wallet
