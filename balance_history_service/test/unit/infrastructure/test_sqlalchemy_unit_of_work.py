from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.domain.entities.trade_record import TradeRecord
from src.exceptions import TradeNotFoundError
from src.infrastructure.persistence.unit_of_work import SQLAlchemyUnitOfWork


def _trade(trade_id: str = "11111111-1111-4111-8111-111111111111") -> TradeRecord:
    return TradeRecord(
        trade_id=trade_id,
        maker_order_id="22222222-2222-4222-8222-222222222222",
        taker_order_id="33333333-3333-4333-8333-333333333333",
        buyer_id="44444444-4444-4444-8444-444444444444",
        seller_id="55555555-5555-4555-8555-555555555555",
        instrument_id="66666666-6666-4666-8666-666666666666",
        quantity=3,
        execution_price=Decimal("9.99"),
        execution_price_currency="USD",
        sequence_number=1,
        executed_at=datetime.now(timezone.utc),
    )


async def test_commit_persists_trade(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    trade = _trade()
    async with SQLAlchemyUnitOfWork(session_factory) as uow:
        await uow.trades.add(trade)
        await uow.commit()

    async with SQLAlchemyUnitOfWork(session_factory) as uow:
        loaded = await uow.trades.get_by_id(trade.trade_id)

    assert loaded.quantity == 3


async def test_rollback_on_exception(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    trade = _trade("77777777-7777-4777-8777-777777777777")

    with pytest.raises(RuntimeError):
        async with SQLAlchemyUnitOfWork(session_factory) as uow:
            await uow.trades.add(trade)
            raise RuntimeError("force rollback")

    async with SQLAlchemyUnitOfWork(session_factory) as uow:
        with pytest.raises(TradeNotFoundError):
            await uow.trades.get_by_id(trade.trade_id)
