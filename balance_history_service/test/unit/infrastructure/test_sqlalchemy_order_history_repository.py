from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.order_history_entry import OrderHistoryEntry
from src.infrastructure.persistence.repositories.sqlalchemy_order_history_repository import (
    SQLAlchemyOrderHistoryRepository,
)


async def test_add_and_list_by_order(
    order_history_repository: SQLAlchemyOrderHistoryRepository,
    session: AsyncSession,
    sample_order_entry: OrderHistoryEntry,
) -> None:
    await order_history_repository.add(sample_order_entry)
    await session.commit()

    entries = await order_history_repository.list_by_order(sample_order_entry.order_id)

    assert len(entries) == 1
    assert entries[0].event_type == "OrderOpened"
    assert entries[0].side == "SELL"
    assert entries[0].price is not None


async def test_list_by_trader(
    order_history_repository: SQLAlchemyOrderHistoryRepository,
    session: AsyncSession,
    sample_order_entry: OrderHistoryEntry,
) -> None:
    await order_history_repository.add(sample_order_entry)
    await session.commit()

    entries = await order_history_repository.list_by_trader(
        sample_order_entry.trader_id
    )
    assert len(entries) == 1
    assert entries[0].entry_id == sample_order_entry.entry_id


async def test_list_empty(
    order_history_repository: SQLAlchemyOrderHistoryRepository,
) -> None:
    assert (
        await order_history_repository.list_by_order(
            "00000000-0000-4000-8000-000000000000"
        )
        == []
    )
