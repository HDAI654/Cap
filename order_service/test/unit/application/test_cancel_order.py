from unittest.mock import AsyncMock

import pytest

from src.application.cancel_order import CancelOrderCommand, CancelOrderHandler
from src.domain.entities.order import Order
from src.domain.events.order_events import OrderCancelled
from src.domain.value_objects.order_status import OrderStatus
from src.domain.value_objects.quantity import Quantity
from src.exceptions import InvalidOrderStateError


async def test_cancels_new_order(
    mock_uow: AsyncMock,
    mock_event_publisher: AsyncMock,
    mock_order_repository: AsyncMock,
    new_limit_order: Order,
) -> None:
    mock_order_repository.get_by_id.return_value = new_limit_order

    handler = CancelOrderHandler(mock_uow, mock_event_publisher)
    await handler.handle(CancelOrderCommand(order_id=new_limit_order.id.value))

    assert new_limit_order.status is OrderStatus.CANCELLED
    mock_order_repository.update.assert_awaited_once_with(new_limit_order)
    mock_uow.commit.assert_awaited_once()
    mock_event_publisher.publish.assert_awaited_once()
    event = mock_event_publisher.publish.await_args.args[0]
    assert isinstance(event, OrderCancelled)
    assert event.order_id == new_limit_order.id.value


async def test_cancels_open_order(
    mock_uow: AsyncMock,
    mock_event_publisher: AsyncMock,
    mock_order_repository: AsyncMock,
    open_order: Order,
) -> None:
    mock_order_repository.get_by_id.return_value = open_order

    handler = CancelOrderHandler(mock_uow, mock_event_publisher)
    await handler.handle(CancelOrderCommand(order_id=open_order.id.value))

    assert open_order.status is OrderStatus.CANCELLED
    mock_uow.commit.assert_awaited_once()


async def test_cancels_partially_filled_order(
    mock_uow: AsyncMock,
    mock_event_publisher: AsyncMock,
    mock_order_repository: AsyncMock,
    partially_filled_order: Order,
) -> None:
    mock_order_repository.get_by_id.return_value = partially_filled_order

    handler = CancelOrderHandler(mock_uow, mock_event_publisher)
    await handler.handle(CancelOrderCommand(order_id=partially_filled_order.id.value))

    assert partially_filled_order.status is OrderStatus.CANCELLED
    assert partially_filled_order.filled_quantity == Quantity(40)
    mock_uow.commit.assert_awaited_once()


async def test_raises_when_already_filled(
    mock_uow: AsyncMock,
    mock_event_publisher: AsyncMock,
    mock_order_repository: AsyncMock,
    filled_order: Order,
) -> None:
    mock_order_repository.get_by_id.return_value = filled_order

    handler = CancelOrderHandler(mock_uow, mock_event_publisher)

    with pytest.raises(InvalidOrderStateError):
        await handler.handle(CancelOrderCommand(order_id=filled_order.id.value))

    mock_order_repository.update.assert_not_awaited()
    mock_uow.commit.assert_not_awaited()
    mock_event_publisher.publish.assert_not_awaited()
