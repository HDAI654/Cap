from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.domain.entities.instrument import Instrument
from src.domain.value_objects.currency import Currency
from src.domain.value_objects.instrument_status import InstrumentStatus
from src.domain.value_objects.money import Money
from src.domain.value_objects.quantity import Quantity
from src.exceptions import InstrumentNotFoundError
from src.infrastructure.persistence.unit_of_work import SQLAlchemyUnitOfWork


def _new_instrument(symbol: str = "AAPL") -> Instrument:
    instrument = Instrument.create(
        symbol=symbol,
        name=f"{symbol} Corp",
        tick_size=Money(Decimal("0.01"), Currency.USD),
        lot_size=Quantity(1),
        minimum_order_quantity=Quantity(1),
        maximum_order_quantity=Quantity(1000),
        currency=Currency.USD,
    )
    instrument.clear_changes()
    return instrument


async def test_commit_persists_instrument(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    instrument = _new_instrument()

    async with SQLAlchemyUnitOfWork(session_factory) as uow:
        await uow.instruments.add(instrument)
        await uow.commit()

    async with SQLAlchemyUnitOfWork(session_factory) as uow:
        loaded = await uow.instruments.get_by_id(instrument.id)

    assert loaded.symbol == "AAPL"
    assert loaded.status is InstrumentStatus.PENDING


async def test_rollback_on_exception_discards_changes(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    instrument = _new_instrument("TSLA")

    with pytest.raises(RuntimeError):
        async with SQLAlchemyUnitOfWork(session_factory) as uow:
            await uow.instruments.add(instrument)
            raise RuntimeError("force rollback")

    async with SQLAlchemyUnitOfWork(session_factory) as uow:
        with pytest.raises(InstrumentNotFoundError):
            await uow.instruments.get_by_id(instrument.id)


async def test_update_and_commit_status(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    instrument = _new_instrument("GOOG")

    async with SQLAlchemyUnitOfWork(session_factory) as uow:
        await uow.instruments.add(instrument)
        await uow.commit()

    async with SQLAlchemyUnitOfWork(session_factory) as uow:
        loaded = await uow.instruments.get_by_id(instrument.id)
        loaded.activate()
        await uow.instruments.update(loaded)
        await uow.commit()

    async with SQLAlchemyUnitOfWork(session_factory) as uow:
        reloaded = await uow.instruments.get_by_id(instrument.id)

    assert reloaded.status is InstrumentStatus.ACTIVE
