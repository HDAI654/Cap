from unittest.mock import AsyncMock

import pytest

from src.application.expire_order import ExpireOrderCommand, ExpireOrderHandler
from src.domain.entities.order import Order
from src.domain.value_objects.order_status import OrderStatus
from src.domain.value_objects.quantity import Quantity
from src.exceptions import InvalidOrderStateError


async def test_expires_open_order(
    mock_uow: AsyncMock,
    mock_order_repository: AsyncMock,
    open_order: Order,
) -> None:
    mock_order_repository.get_by_id.return_value = open_order

    handler = ExpireOrderHandler(mock_uow)
    await handler.handle(ExpireOrderCommand(order_id=open_order.id.value))

    assert open_order.status is OrderStatus.EXPIRED
    mock_order_repository.update.assert_awaited_once_with(open_order)
    mock_uow.commit.assert_awaited_once()


async def test_expires_partially_filled_order(
    mock_uow: AsyncMock,
    mock_order_repository: AsyncMock,
    partially_filled_order: Order,
) -> None:
    mock_order_repository.get_by_id.return_value = partially_filled_order

    handler = ExpireOrderHandler(mock_uow)
    await handler.handle(ExpireOrderCommand(order_id=partially_filled_order.id.value))

    assert partially_filled_order.status is OrderStatus.EXPIRED
    assert partially_filled_order.filled_quantity == Quantity(40)
    mock_uow.commit.assert_awaited_once()


async def test_raises_when_still_new(
    mock_uow: AsyncMock,
    mock_order_repository: AsyncMock,
    new_limit_order: Order,
) -> None:
    mock_order_repository.get_by_id.return_value = new_limit_order

    handler = ExpireOrderHandler(mock_uow)

    with pytest.raises(InvalidOrderStateError):
        await handler.handle(ExpireOrderCommand(order_id=new_limit_order.id.value))

    mock_order_repository.update.assert_not_awaited()
    mock_uow.commit.assert_not_awaited()


async def test_raises_when_already_filled(
    mock_uow: AsyncMock,
    mock_order_repository: AsyncMock,
    filled_order: Order,
) -> None:
    mock_order_repository.get_by_id.return_value = filled_order

    handler = ExpireOrderHandler(mock_uow)

    with pytest.raises(InvalidOrderStateError):
        await handler.handle(ExpireOrderCommand(order_id=filled_order.id.value))

    mock_order_repository.update.assert_not_awaited()
