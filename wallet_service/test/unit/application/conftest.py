import pytest
from unittest.mock import AsyncMock
from src.domain.entities.wallet import Wallet
from src.domain.ports.unit_of_work import UnitOfWork
from src.domain.ports.wallet_repository import WalletRepository
from src.domain.value_objects.trader_id import TraderId


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
def mock_uow(mock_wallet_repository) -> AsyncMock:
    uow = AsyncMock(spec=UnitOfWork)
    uow.wallets = mock_wallet_repository

    # Mock async context manager methods
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=None)
    uow.commit = AsyncMock()
    uow.rollback = AsyncMock()

    return uow


@pytest.fixture
def active_wallet() -> Wallet:
    trader_id = TraderId("trader-123")
    wallet = Wallet.create(trader_id)
    return wallet


@pytest.fixture
def locked_wallet() -> Wallet:
    trader_id = TraderId("trader-123")
    wallet = Wallet.create(trader_id)
    wallet.lock()
    return wallet


@pytest.fixture
def closed_wallet() -> Wallet:
    """Return a wallet in CLOSED status."""
    trader_id = TraderId("trader-123")
    wallet = Wallet.create(trader_id)
    wallet.close()
    return wallet
