from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.instrument import Instrument
from src.domain.value_objects.currency import Currency
from src.domain.value_objects.instrument_id import InstrumentId
from src.domain.value_objects.instrument_status import InstrumentStatus
from src.domain.value_objects.money import Money
from src.domain.value_objects.quantity import Quantity
from src.exceptions import InstrumentNotFoundError
from src.infrastructure.persistence.repositories.sqlalchemy_instrument_repository import (
    SQLAlchemyInstrumentRepository,
)


async def test_add_and_get_by_id(
    repository: SQLAlchemyInstrumentRepository,
    session: AsyncSession,
    sample_instrument: Instrument,
) -> None:
    await repository.add(sample_instrument)
    await session.commit()

    loaded = await repository.get_by_id(sample_instrument.id)

    assert loaded.id == sample_instrument.id
    assert loaded.symbol == "AAPL"
    assert loaded.name == "Apple Inc."
    assert loaded.tick_size.amount == Decimal("0.01")
    assert loaded.tick_size.currency is Currency.USD
    assert loaded.lot_size == Quantity(1)
    assert loaded.minimum_order_quantity == Quantity(1)
    assert loaded.maximum_order_quantity == Quantity(10000)
    assert loaded.currency is Currency.USD
    assert loaded.total_shares == Quantity(0)
    assert loaded.status is InstrumentStatus.PENDING
    assert loaded.created_at is not None
    assert loaded.updated_at is not None


async def test_get_by_id_raises_when_missing(
    repository: SQLAlchemyInstrumentRepository,
) -> None:
    missing = InstrumentId.generate()

    with pytest.raises(InstrumentNotFoundError, match=missing.value):
        await repository.get_by_id(missing)


async def test_get_by_symbol_returns_instrument(
    repository: SQLAlchemyInstrumentRepository,
    session: AsyncSession,
    sample_instrument: Instrument,
) -> None:
    await repository.add(sample_instrument)
    await session.commit()

    loaded = await repository.get_by_symbol("aapl")

    assert loaded is not None
    assert loaded.id == sample_instrument.id
    assert loaded.symbol == "AAPL"


async def test_get_by_symbol_returns_none_when_missing(
    repository: SQLAlchemyInstrumentRepository,
) -> None:
    assert await repository.get_by_symbol("NOSYMBOL") is None


async def test_list_all_ordered_by_symbol(
    repository: SQLAlchemyInstrumentRepository,
    session: AsyncSession,
    sample_instrument: Instrument,
    other_instrument: Instrument,
) -> None:
    await repository.add(other_instrument)
    await repository.add(sample_instrument)
    await session.commit()

    listed = await repository.list_all()

    assert len(listed) == 2
    assert listed[0].symbol == "AAPL"
    assert listed[1].symbol == "MSFT"


async def test_list_all_empty(
    repository: SQLAlchemyInstrumentRepository,
) -> None:
    assert await repository.list_all() == []


async def test_update_status_change(
    repository: SQLAlchemyInstrumentRepository,
    session: AsyncSession,
    sample_instrument: Instrument,
) -> None:
    await repository.add(sample_instrument)
    await session.commit()

    sample_instrument.activate()
    await repository.update(sample_instrument)
    await session.commit()

    loaded = await repository.get_by_id(sample_instrument.id)
    assert loaded.status is InstrumentStatus.ACTIVE


async def test_update_shares_change(
    repository: SQLAlchemyInstrumentRepository,
    session: AsyncSession,
    sample_instrument: Instrument,
) -> None:
    await repository.add(sample_instrument)
    await session.commit()

    sample_instrument.allocate_shares(Quantity(2500))
    await repository.update(sample_instrument)
    await session.commit()

    loaded = await repository.get_by_id(sample_instrument.id)
    assert loaded.total_shares == Quantity(2500)


async def test_update_missing_raises(
    repository: SQLAlchemyInstrumentRepository,
    sample_instrument: Instrument,
) -> None:
    sample_instrument.activate()

    with pytest.raises(InstrumentNotFoundError):
        await repository.update(sample_instrument)


async def test_partial_update_does_not_overwrite_unchanged_fields(
    repository: SQLAlchemyInstrumentRepository,
    session: AsyncSession,
    sample_instrument: Instrument,
) -> None:
    sample_instrument.allocate_shares(Quantity(100))
    sample_instrument.clear_changes()
    await repository.add(sample_instrument)
    await session.commit()

    sample_instrument.activate()
    await repository.update(sample_instrument)
    await session.commit()

    loaded = await repository.get_by_id(sample_instrument.id)
    assert loaded.status is InstrumentStatus.ACTIVE
    assert loaded.total_shares == Quantity(100)
