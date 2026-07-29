from decimal import Decimal
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.entities.wallet import Wallet
from src.domain.value_objects.currency import Currency
from src.domain.value_objects.instrument_id import InstrumentId
from src.domain.value_objects.money import Money
from src.domain.value_objects.quantity import Quantity
from src.domain.value_objects.trader_id import TraderId
from src.domain.value_objects.wallet_id import WalletId
from src.domain.value_objects.wallet_status import WalletStatus
from src.exceptions import WalletNotFoundError
from src.infrastructure.persistence.repositories.sqlalchemy_wallet_repository import (
    SQLAlchemyWalletRepository,
)

# ---------------------------------------------------------------------------
# add / get_by_id
# ---------------------------------------------------------------------------


async def test_add_and_get_by_id_returns_empty_wallet(
    repository: SQLAlchemyWalletRepository,
    session: AsyncSession,
    empty_wallet: Wallet,
) -> None:
    await repository.add(empty_wallet)
    await session.commit()

    loaded = await repository.get_by_id(empty_wallet.id)

    assert loaded.id == empty_wallet.id
    assert loaded.trader_id == empty_wallet.trader_id
    assert loaded.status == WalletStatus.ACTIVE
    assert loaded.cash_balances == ()
    assert loaded.holdings == ()


async def test_add_and_get_by_id_preserves_cash_and_holdings(
    repository: SQLAlchemyWalletRepository,
    session: AsyncSession,
    funded_wallet: Wallet,
) -> None:
    await repository.add(funded_wallet)
    await session.commit()

    loaded = await repository.get_by_id(funded_wallet.id)

    assert len(loaded.cash_balances) == 1
    usd = loaded.cash_balances[0]
    assert usd.currency == Currency.USD
    assert usd.available.amount == Decimal("100.00")
    assert usd.reserved.amount == Decimal("0.00")

    assert len(loaded.holdings) == 1
    holding = loaded.holdings[0]
    assert holding.available.value == 10
    assert holding.reserved.value == 0
    assert holding.average_cost.amount == Decimal("25.50")
    assert holding.average_cost.currency == Currency.USD


async def test_get_by_id_raises_when_missing(
    repository: SQLAlchemyWalletRepository,
) -> None:
    missing_id = WalletId.generate()

    with pytest.raises(WalletNotFoundError, match=missing_id.value):
        await repository.get_by_id(missing_id)


# ---------------------------------------------------------------------------
# get_by_trader_id / exists_by_trader_id
# ---------------------------------------------------------------------------


async def test_get_by_trader_id_returns_wallet(
    repository: SQLAlchemyWalletRepository,
    session: AsyncSession,
    empty_wallet: Wallet,
) -> None:
    await repository.add(empty_wallet)
    await session.commit()

    loaded = await repository.get_by_trader_id(empty_wallet.trader_id)

    assert loaded.id == empty_wallet.id
    assert loaded.trader_id == empty_wallet.trader_id


async def test_get_by_trader_id_raises_when_missing(
    repository: SQLAlchemyWalletRepository,
) -> None:
    missing_trader = TraderId.generate()

    with pytest.raises(WalletNotFoundError, match=missing_trader.value):
        await repository.get_by_trader_id(missing_trader)


async def test_exists_by_trader_id_true_and_false(
    repository: SQLAlchemyWalletRepository,
    session: AsyncSession,
    empty_wallet: Wallet,
) -> None:
    assert await repository.exists_by_trader_id(empty_wallet.trader_id) is False

    await repository.add(empty_wallet)
    await session.commit()

    assert await repository.exists_by_trader_id(empty_wallet.trader_id) is True
    assert await repository.exists_by_trader_id(TraderId.generate()) is False


# ---------------------------------------------------------------------------
# update — status
# ---------------------------------------------------------------------------


async def test_update_persists_status_change(
    repository: SQLAlchemyWalletRepository,
    session: AsyncSession,
    empty_wallet: Wallet,
) -> None:
    await repository.add(empty_wallet)
    await session.commit()

    wallet = await repository.get_by_id(empty_wallet.id)
    wallet.lock()
    await repository.update(wallet)
    await session.commit()
    wallet.clear_changes()

    reloaded = await repository.get_by_id(empty_wallet.id)
    assert reloaded.status == WalletStatus.LOCKED

    reloaded.activate()
    await repository.update(reloaded)
    await session.commit()

    final = await repository.get_by_id(empty_wallet.id)
    assert final.status == WalletStatus.ACTIVE


# ---------------------------------------------------------------------------
# update — cash
# ---------------------------------------------------------------------------


async def test_update_creates_cash_balance(
    repository: SQLAlchemyWalletRepository,
    session: AsyncSession,
    empty_wallet: Wallet,
) -> None:
    await repository.add(empty_wallet)
    await session.commit()

    wallet = await repository.get_by_id(empty_wallet.id)
    wallet.deposit_cash(Money(Decimal("50.25"), Currency.USD))
    await repository.update(wallet)
    await session.commit()

    loaded = await repository.get_by_id(empty_wallet.id)
    assert len(loaded.cash_balances) == 1
    assert loaded.cash_balances[0].available.amount == Decimal("50.25")
    assert loaded.cash_balances[0].reserved.amount == Decimal("0.00")


async def test_update_modifies_existing_cash_balance(
    repository: SQLAlchemyWalletRepository,
    session: AsyncSession,
    funded_wallet: Wallet,
) -> None:
    await repository.add(funded_wallet)
    await session.commit()

    wallet = await repository.get_by_id(funded_wallet.id)
    wallet.reserve_cash(Money(Decimal("30.00"), Currency.USD))
    wallet.withdraw_cash(Money(Decimal("10.00"), Currency.USD))
    await repository.update(wallet)
    await session.commit()

    loaded = await repository.get_by_id(funded_wallet.id)
    usd = next(b for b in loaded.cash_balances if b.currency == Currency.USD)
    assert usd.available.amount == Decimal("60.00")
    assert usd.reserved.amount == Decimal("30.00")


async def test_update_adds_second_currency(
    repository: SQLAlchemyWalletRepository,
    session: AsyncSession,
    funded_wallet: Wallet,
) -> None:
    await repository.add(funded_wallet)
    await session.commit()

    wallet = await repository.get_by_id(funded_wallet.id)
    wallet.deposit_cash(Money(Decimal("75.00"), Currency.EUR))
    await repository.update(wallet)
    await session.commit()

    loaded = await repository.get_by_id(funded_wallet.id)
    currencies = {b.currency for b in loaded.cash_balances}
    assert currencies == {Currency.USD, Currency.EUR}


# ---------------------------------------------------------------------------
# update — holdings
# ---------------------------------------------------------------------------


async def test_update_creates_holding(
    repository: SQLAlchemyWalletRepository,
    session: AsyncSession,
    empty_wallet: Wallet,
    instrument_id: InstrumentId,
) -> None:
    await repository.add(empty_wallet)
    await session.commit()

    wallet = await repository.get_by_id(empty_wallet.id)
    wallet.add_holding(
        instrument_id,
        Quantity(5),
        Money(Decimal("12.00"), Currency.USD),
    )
    await repository.update(wallet)
    await session.commit()

    loaded = await repository.get_by_id(empty_wallet.id)
    assert len(loaded.holdings) == 1
    holding = loaded.holdings[0]
    assert holding.instrument_id == instrument_id
    assert holding.available.value == 5
    assert holding.average_cost.amount == Decimal("12.00")


async def test_update_modifies_existing_holding(
    repository: SQLAlchemyWalletRepository,
    session: AsyncSession,
    funded_wallet: Wallet,
) -> None:
    await repository.add(funded_wallet)
    await session.commit()

    wallet = await repository.get_by_id(funded_wallet.id)
    instrument_id = wallet.holdings[0].instrument_id
    wallet.reserve_holding(instrument_id, Quantity(4))
    await repository.update(wallet)
    await session.commit()

    loaded = await repository.get_by_id(funded_wallet.id)
    holding = loaded.holdings[0]
    assert holding.available.value == 6
    assert holding.reserved.value == 4


async def test_update_removes_holding_when_quantity_reaches_zero(
    repository: SQLAlchemyWalletRepository,
    session: AsyncSession,
    funded_wallet: Wallet,
) -> None:
    await repository.add(funded_wallet)
    await session.commit()

    wallet = await repository.get_by_id(funded_wallet.id)
    instrument_id = wallet.holdings[0].instrument_id
    wallet.remove_holding(instrument_id, Quantity(10))
    await repository.update(wallet)
    await session.commit()

    loaded = await repository.get_by_id(funded_wallet.id)
    assert loaded.holdings == ()


async def test_update_removes_holding_after_consume_reserved(
    repository: SQLAlchemyWalletRepository,
    session: AsyncSession,
    funded_wallet: Wallet,
) -> None:
    await repository.add(funded_wallet)
    await session.commit()

    wallet = await repository.get_by_id(funded_wallet.id)
    instrument_id = wallet.holdings[0].instrument_id
    wallet.reserve_holding(instrument_id, Quantity(10))
    wallet.consume_reserved_holding(instrument_id, Quantity(10))
    await repository.update(wallet)
    await session.commit()

    loaded = await repository.get_by_id(funded_wallet.id)
    assert loaded.holdings == ()


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------


async def test_delete_removes_wallet(
    repository: SQLAlchemyWalletRepository,
    session: AsyncSession,
    funded_wallet: Wallet,
) -> None:
    await repository.add(funded_wallet)
    await session.commit()

    await repository.delete(funded_wallet.id)
    await session.commit()

    with pytest.raises(WalletNotFoundError):
        await repository.get_by_id(funded_wallet.id)
    assert await repository.exists_by_trader_id(funded_wallet.trader_id) is False


async def test_delete_raises_when_missing(
    repository: SQLAlchemyWalletRepository,
) -> None:
    missing_id = WalletId.generate()

    with pytest.raises(WalletNotFoundError, match=missing_id.value):
        await repository.delete(missing_id)


# ---------------------------------------------------------------------------
# combined change-tracker path
# ---------------------------------------------------------------------------


async def test_update_applies_status_cash_and_holding_changes_together(
    repository: SQLAlchemyWalletRepository,
    session: AsyncSession,
    empty_wallet: Wallet,
    instrument_id: InstrumentId,
) -> None:
    await repository.add(empty_wallet)
    await session.commit()

    wallet = await repository.get_by_id(empty_wallet.id)
    wallet.deposit_cash(Money(Decimal("200.00"), Currency.USD))
    wallet.add_holding(
        instrument_id,
        Quantity(3),
        Money(Decimal("40.00"), Currency.USD),
    )
    await repository.update(wallet)
    await session.commit()
    wallet.clear_changes()

    wallet = await repository.get_by_id(empty_wallet.id)
    wallet.reserve_cash(Money(Decimal("50.00"), Currency.USD))
    wallet.reserve_holding(instrument_id, Quantity(1))
    wallet.lock()
    await repository.update(wallet)
    await session.commit()

    loaded = await repository.get_by_id(empty_wallet.id)
    assert loaded.status == WalletStatus.LOCKED
    usd = loaded.cash_balances[0]
    assert usd.available.amount == Decimal("150.00")
    assert usd.reserved.amount == Decimal("50.00")
    holding = loaded.holdings[0]
    assert holding.available.value == 2
    assert holding.reserved.value == 1
