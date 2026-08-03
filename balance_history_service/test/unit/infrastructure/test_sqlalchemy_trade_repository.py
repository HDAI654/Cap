from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.trade_record import TradeRecord
from src.exceptions import TradeNotFoundError
from src.infrastructure.persistence.repositories.sqlalchemy_trade_repository import (
    SQLAlchemyTradeRepository,
)


async def test_add_and_get_by_id(
    trade_repository: SQLAlchemyTradeRepository,
    session: AsyncSession,
    sample_trade: TradeRecord,
) -> None:
    await trade_repository.add(sample_trade)
    await session.commit()

    loaded = await trade_repository.get_by_id(sample_trade.trade_id)

    assert loaded.trade_id == sample_trade.trade_id
    assert loaded.quantity == 10
    assert loaded.execution_price == Decimal("100.50")
    assert loaded.buyer_id == sample_trade.buyer_id
    assert loaded.seller_id == sample_trade.seller_id


async def test_get_by_id_raises_when_missing(
    trade_repository: SQLAlchemyTradeRepository,
) -> None:
    with pytest.raises(TradeNotFoundError):
        await trade_repository.get_by_id("99999999-9999-4999-8999-999999999999")


async def test_exists(
    trade_repository: SQLAlchemyTradeRepository,
    session: AsyncSession,
    sample_trade: TradeRecord,
) -> None:
    assert await trade_repository.exists(sample_trade.trade_id) is False
    await trade_repository.add(sample_trade)
    await session.commit()
    assert await trade_repository.exists(sample_trade.trade_id) is True


async def test_list_by_trader_includes_buyer_and_seller(
    trade_repository: SQLAlchemyTradeRepository,
    session: AsyncSession,
    sample_trade: TradeRecord,
) -> None:
    await trade_repository.add(sample_trade)
    await session.commit()

    as_buyer = await trade_repository.list_by_trader(sample_trade.buyer_id)
    as_seller = await trade_repository.list_by_trader(sample_trade.seller_id)

    assert len(as_buyer) == 1
    assert len(as_seller) == 1
    assert await trade_repository.list_by_trader(
        "00000000-0000-4000-8000-000000000000"
    ) == []


async def test_list_by_instrument(
    trade_repository: SQLAlchemyTradeRepository,
    session: AsyncSession,
    sample_trade: TradeRecord,
) -> None:
    await trade_repository.add(sample_trade)
    await session.commit()

    listed = await trade_repository.list_by_instrument(sample_trade.instrument_id)
    assert len(listed) == 1
    assert listed[0].trade_id == sample_trade.trade_id
