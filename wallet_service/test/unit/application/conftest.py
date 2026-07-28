from unittest.mock import AsyncMock
import pytest
from src.domain.entities.wallet import Wallet
from src.domain.ports.unit_of_work import UnitOfWork
from src.domain.ports.wallet_repository import WalletRepository
from src.domain.value_objects.trader_id import TraderId
from src.domain.value_objects.wallet_id import WalletId
from src.domain.value_objects.wallet_status import WalletStatus

# ---------------------------------------------------------------------------
# Repository & Unit of Work
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_wallet_repository() -> AsyncMock:
    repo = AsyncMock(spec=WalletRepository)
    repo.add = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.get_by_trader_id = AsyncMock()
    repo.update = AsyncMock()
    repo.delete = AsyncMock()
    repo.exists_by_trader_id = AsyncMock()
    return repo


@pytest.fixture
def mock_uow(mock_wallet_repository: AsyncMock) -> AsyncMock:
    uow = AsyncMock(spec=UnitOfWork)
    uow.wallets = mock_wallet_repository
    uow.commit = AsyncMock()
    uow.rollback = AsyncMock()
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=None)
    return uow


# ---------------------------------------------------------------------------
# Identifiers
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_wallet_id() -> WalletId:
    return WalletId.generate()


@pytest.fixture
def sample_trader_id() -> TraderId:
    return TraderId.generate()


# ---------------------------------------------------------------------------
# Real wallet aggregates
# ---------------------------------------------------------------------------


@pytest.fixture
def active_wallet(
    sample_wallet_id: WalletId,
    sample_trader_id: TraderId,
) -> Wallet:
    wallet = Wallet(
        id=sample_wallet_id,
        trader_id=sample_trader_id,
        status=WalletStatus.ACTIVE,
    )
    wallet.clear_changes()
    return wallet


@pytest.fixture
def locked_wallet(
    sample_wallet_id: WalletId,
    sample_trader_id: TraderId,
) -> Wallet:
    wallet = Wallet(
        id=sample_wallet_id,
        trader_id=sample_trader_id,
        status=WalletStatus.LOCKED,
    )
    wallet.clear_changes()
    return wallet


@pytest.fixture
def closed_wallet(
    sample_wallet_id: WalletId,
    sample_trader_id: TraderId,
) -> Wallet:
    wallet = Wallet(
        id=sample_wallet_id,
        trader_id=sample_trader_id,
        status=WalletStatus.CLOSED,
    )
    wallet.clear_changes()
    return wallet
