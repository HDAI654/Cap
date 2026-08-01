from unittest.mock import AsyncMock

import pytest

from src.application.reject_order import RejectOrderCommand, RejectOrderHandler
from src.domain.entities.order import Order
from src.domain.events.order_events import OrderRejected
from src.domain.value_objects.order_status import OrderStatus
from src.exceptions import InvalidOrderStateError


async def test_rejects_new_order(
    mock_uow: AsyncMock,
    mock_event_publisher: AsyncMock,
    mock_order_repository: AsyncMock,
    new_limit_order: Order,
) -> None:
    mock_order_repository.get_by_id.return_value = new_limit_order

    handler = RejectOrderHandler(mock_uow, mock_event_publisher)
    await handler.handle(RejectOrderCommand(order_id=new_limit_order.id.value))

    assert new_limit_order.status is OrderStatus.REJECTED
    mock_order_repository.update.assert_awaited_once_with(new_limit_order)
    mock_uow.commit.assert_awaited_once()
    mock_event_publisher.publish.assert_awaited_once()
    event = mock_event_publisher.publish.await_args.args[0]
    assert isinstance(event, OrderRejected)
    assert event.order_id == new_limit_order.id.value


async def test_raises_when_already_open(
    mock_uow: AsyncMock,
    mock_event_publisher: AsyncMock,
    mock_order_repository: AsyncMock,
    open_order: Order,
) -> None:
    mock_order_repository.get_by_id.return_value = open_order

    handler = RejectOrderHandler(mock_uow, mock_event_publisher)

    with pytest.raises(InvalidOrderStateError):
        await handler.handle(RejectOrderCommand(order_id=open_order.id.value))

    mock_order_repository.update.assert_not_awaited()
    mock_uow.commit.assert_not_awaited()
    mock_event_publisher.publish.assert_not_awaited()
