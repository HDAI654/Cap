from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.order import Order
from src.domain.value_objects.currency import Currency
from src.domain.value_objects.idempotency_key import IdempotencyKey
from src.domain.value_objects.instrument_id import InstrumentId
from src.domain.value_objects.order_id import OrderId
from src.domain.value_objects.order_status import OrderStatus
from src.domain.value_objects.order_type import OrderType
from src.domain.value_objects.quantity import Quantity
from src.domain.value_objects.trader_id import TraderId
from src.exceptions import OrderNotFoundError
from src.infrastructure.persistence.repositories.sqlalchemy_order_repository import (
    SQLAlchemyOrderRepository,
)

# ---------------------------------------------------------------------------
# add / get_by_id
# ---------------------------------------------------------------------------


async def test_add_and_get_by_id_returns_limit_order(
    repository: SQLAlchemyOrderRepository,
    session: AsyncSession,
    limit_order: Order,
) -> None:
    await repository.add(limit_order)
    await session.commit()

    loaded = await repository.get_by_id(limit_order.id)

    assert loaded.id == limit_order.id
    assert loaded.trader_id == limit_order.trader_id
    assert loaded.instrument_id == limit_order.instrument_id
    assert loaded.side == limit_order.side
    assert loaded.order_type is OrderType.LIMIT
    assert loaded.quantity == Quantity(100)
    assert loaded.filled_quantity == Quantity(0)
    assert loaded.remaining_quantity == Quantity(100)
    assert loaded.limit_price is not None
    assert loaded.limit_price.amount == Decimal("10.50")
    assert loaded.limit_price.currency == Currency.USD
    assert loaded.status is OrderStatus.NEW
    assert loaded.idempotency_key.value == "infra-limit-001"
    assert loaded.created_at is not None
    assert loaded.updated_at is not None


async def test_add_and_get_by_id_returns_market_order_without_price(
    repository: SQLAlchemyOrderRepository,
    session: AsyncSession,
    market_order: Order,
) -> None:
    await repository.add(market_order)
    await session.commit()

    loaded = await repository.get_by_id(market_order.id)

    assert loaded.order_type is OrderType.MARKET
    assert loaded.limit_price is None
    assert loaded.quantity == Quantity(50)
    assert loaded.status is OrderStatus.NEW


async def test_get_by_id_raises_when_missing(
    repository: SQLAlchemyOrderRepository,
) -> None:
    missing_id = OrderId.generate()

    with pytest.raises(OrderNotFoundError, match=missing_id.value):
        await repository.get_by_id(missing_id)


# ---------------------------------------------------------------------------
# get_by_idempotency_key
# ---------------------------------------------------------------------------


async def test_get_by_idempotency_key_returns_order(
    repository: SQLAlchemyOrderRepository,
    session: AsyncSession,
    limit_order: Order,
) -> None:
    await repository.add(limit_order)
    await session.commit()

    loaded = await repository.get_by_idempotency_key(
        limit_order.trader_id,
        limit_order.idempotency_key,
    )

    assert loaded is not None
    assert loaded.id == limit_order.id
    assert loaded.idempotency_key == limit_order.idempotency_key


async def test_get_by_idempotency_key_returns_none_when_missing(
    repository: SQLAlchemyOrderRepository,
    trader_id: TraderId,
) -> None:
    result = await repository.get_by_idempotency_key(
        trader_id,
        IdempotencyKey("does-not-exist"),
    )

    assert result is None


async def test_get_by_idempotency_key_is_scoped_to_trader(
    repository: SQLAlchemyOrderRepository,
    session: AsyncSession,
    limit_order: Order,
) -> None:
    await repository.add(limit_order)
    await session.commit()

    other_trader = TraderId.generate()
    result = await repository.get_by_idempotency_key(
        other_trader,
        limit_order.idempotency_key,
    )

    assert result is None


# ---------------------------------------------------------------------------
# list_by_trader
# ---------------------------------------------------------------------------


async def test_list_by_trader_returns_orders(
    repository: SQLAlchemyOrderRepository,
    session: AsyncSession,
    limit_order: Order,
    market_order: Order,
) -> None:
    await repository.add(limit_order)
    await repository.add(market_order)
    await session.commit()

    orders = await repository.list_by_trader(limit_order.trader_id)

    assert len(orders) == 2
    ids = {o.id for o in orders}
    assert limit_order.id in ids
    assert market_order.id in ids


async def test_list_by_trader_returns_empty_when_none(
    repository: SQLAlchemyOrderRepository,
    trader_id: TraderId,
) -> None:
    orders = await repository.list_by_trader(trader_id)

    assert orders == []


async def test_list_by_trader_does_not_include_other_traders(
    repository: SQLAlchemyOrderRepository,
    session: AsyncSession,
    limit_order: Order,
    instrument_id: InstrumentId,
) -> None:
    other = Order.create(
        trader_id=TraderId.generate(),
        instrument_id=instrument_id,
        side=limit_order.side,
        order_type=OrderType.LIMIT,
        time_in_force=limit_order.time_in_force,
        quantity=Quantity(5),
        idempotency_key=IdempotencyKey("other-trader-key"),
        limit_price=limit_order.limit_price,
    )
    other.clear_changes()

    await repository.add(limit_order)
    await repository.add(other)
    await session.commit()

    orders = await repository.list_by_trader(limit_order.trader_id)

    assert len(orders) == 1
    assert orders[0].id == limit_order.id


# ---------------------------------------------------------------------------
# update — status
# ---------------------------------------------------------------------------


async def test_update_persists_status_change(
    repository: SQLAlchemyOrderRepository,
    session: AsyncSession,
    limit_order: Order,
) -> None:
    await repository.add(limit_order)
    await session.commit()

    order = await repository.get_by_id(limit_order.id)
    order.open()
    await repository.update(order)
    await session.commit()
    order.clear_changes()

    reloaded = await repository.get_by_id(limit_order.id)
    assert reloaded.status is OrderStatus.OPEN

    reloaded.cancel()
    await repository.update(reloaded)
    await session.commit()

    final = await repository.get_by_id(limit_order.id)
    assert final.status is OrderStatus.CANCELLED


async def test_update_persists_reject(
    repository: SQLAlchemyOrderRepository,
    session: AsyncSession,
    limit_order: Order,
) -> None:
    await repository.add(limit_order)
    await session.commit()

    order = await repository.get_by_id(limit_order.id)
    order.reject()
    await repository.update(order)
    await session.commit()

    loaded = await repository.get_by_id(limit_order.id)
    assert loaded.status is OrderStatus.REJECTED


async def test_update_persists_expire(
    repository: SQLAlchemyOrderRepository,
    session: AsyncSession,
    limit_order: Order,
) -> None:
    await repository.add(limit_order)
    await session.commit()

    order = await repository.get_by_id(limit_order.id)
    order.open()
    await repository.update(order)
    await session.commit()
    order.clear_changes()

    order = await repository.get_by_id(limit_order.id)
    order.expire()
    await repository.update(order)
    await session.commit()

    loaded = await repository.get_by_id(limit_order.id)
    assert loaded.status is OrderStatus.EXPIRED


# ---------------------------------------------------------------------------
# update — fills
# ---------------------------------------------------------------------------


async def test_update_persists_partial_fill(
    repository: SQLAlchemyOrderRepository,
    session: AsyncSession,
    limit_order: Order,
) -> None:
    await repository.add(limit_order)
    await session.commit()

    order = await repository.get_by_id(limit_order.id)
    order.open()
    order.fill(Quantity(40))
    await repository.update(order)
    await session.commit()

    loaded = await repository.get_by_id(limit_order.id)
    assert loaded.status is OrderStatus.PARTIALLY_FILLED
    assert loaded.filled_quantity == Quantity(40)
    assert loaded.remaining_quantity == Quantity(60)


async def test_update_persists_full_fill(
    repository: SQLAlchemyOrderRepository,
    session: AsyncSession,
    limit_order: Order,
) -> None:
    await repository.add(limit_order)
    await session.commit()

    order = await repository.get_by_id(limit_order.id)
    order.open()
    order.fill(Quantity(100))
    await repository.update(order)
    await session.commit()

    loaded = await repository.get_by_id(limit_order.id)
    assert loaded.status is OrderStatus.FILLED
    assert loaded.filled_quantity == Quantity(100)
    assert loaded.remaining_quantity == Quantity(0)


async def test_update_persists_sequential_fills(
    repository: SQLAlchemyOrderRepository,
    session: AsyncSession,
    limit_order: Order,
) -> None:
    await repository.add(limit_order)
    await session.commit()

    order = await repository.get_by_id(limit_order.id)
    order.open()
    order.fill(Quantity(30))
    await repository.update(order)
    await session.commit()
    order.clear_changes()

    order = await repository.get_by_id(limit_order.id)
    order.fill(Quantity(70))
    await repository.update(order)
    await session.commit()

    loaded = await repository.get_by_id(limit_order.id)
    assert loaded.status is OrderStatus.FILLED
    assert loaded.filled_quantity == Quantity(100)


async def test_update_raises_when_missing(
    repository: SQLAlchemyOrderRepository,
    limit_order: Order,
) -> None:
    with pytest.raises(OrderNotFoundError, match=limit_order.id.value):
        await repository.update(limit_order)


# ---------------------------------------------------------------------------
# combined lifecycle path
# ---------------------------------------------------------------------------


async def test_full_lifecycle_open_partial_fill_cancel(
    repository: SQLAlchemyOrderRepository,
    session: AsyncSession,
    limit_order: Order,
) -> None:
    await repository.add(limit_order)
    await session.commit()

    order = await repository.get_by_id(limit_order.id)
    order.open()
    await repository.update(order)
    await session.commit()
    order.clear_changes()

    order = await repository.get_by_id(limit_order.id)
    order.fill(Quantity(25))
    await repository.update(order)
    await session.commit()
    order.clear_changes()

    order = await repository.get_by_id(limit_order.id)
    assert order.status is OrderStatus.PARTIALLY_FILLED
    assert order.filled_quantity == Quantity(25)

    order.cancel()
    await repository.update(order)
    await session.commit()

    loaded = await repository.get_by_id(limit_order.id)
    assert loaded.status is OrderStatus.CANCELLED
    assert loaded.filled_quantity == Quantity(25)
