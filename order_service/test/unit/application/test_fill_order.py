from unittest.mock import AsyncMock

import pytest

from src.application.fill_order import FillOrderCommand, FillOrderHandler
from src.domain.entities.order import Order
from src.domain.events.order_events import OrderFilled
from src.domain.value_objects.order_status import OrderStatus
from src.domain.value_objects.quantity import Quantity
from src.exceptions import InvalidOrderFillError, InvalidOrderStateError


async def test_partial_fill(
    mock_uow: AsyncMock,
    mock_event_publisher: AsyncMock,
    mock_order_repository: AsyncMock,
    open_order: Order,
) -> None:
    mock_order_repository.get_by_id.return_value = open_order

    handler = FillOrderHandler(mock_uow, mock_event_publisher)
    await handler.handle(
        FillOrderCommand(order_id=open_order.id.value, fill_quantity=40)
    )

    assert open_order.filled_quantity == Quantity(40)
    assert open_order.remaining_quantity == Quantity(60)
    assert open_order.status is OrderStatus.PARTIALLY_FILLED
    mock_order_repository.update.assert_awaited_once_with(open_order)
    mock_uow.commit.assert_awaited_once()
    mock_event_publisher.publish.assert_awaited_once()
    event = mock_event_publisher.publish.await_args.args[0]
    assert isinstance(event, OrderFilled)
    assert event.fill_quantity == 40
    assert event.filled_quantity == 40
    assert event.status == OrderStatus.PARTIALLY_FILLED.value


async def test_full_fill(
    mock_uow: AsyncMock,
    mock_event_publisher: AsyncMock,
    mock_order_repository: AsyncMock,
    open_order: Order,
) -> None:
    mock_order_repository.get_by_id.return_value = open_order

    handler = FillOrderHandler(mock_uow, mock_event_publisher)
    await handler.handle(
        FillOrderCommand(order_id=open_order.id.value, fill_quantity=100)
    )

    assert open_order.filled_quantity == Quantity(100)
    assert open_order.status is OrderStatus.FILLED
    mock_order_repository.update.assert_awaited_once()
    mock_uow.commit.assert_awaited_once()
    mock_event_publisher.publish.assert_awaited_once()
    event = mock_event_publisher.publish.await_args.args[0]
    assert isinstance(event, OrderFilled)
    assert event.status == OrderStatus.FILLED.value


async def test_fill_to_complete_after_partial(
    mock_uow: AsyncMock,
    mock_event_publisher: AsyncMock,
    mock_order_repository: AsyncMock,
    partially_filled_order: Order,
) -> None:
    mock_order_repository.get_by_id.return_value = partially_filled_order

    handler = FillOrderHandler(mock_uow, mock_event_publisher)
    await handler.handle(
        FillOrderCommand(
            order_id=partially_filled_order.id.value,
            fill_quantity=60,
        )
    )

    assert partially_filled_order.status is OrderStatus.FILLED
    assert partially_filled_order.filled_quantity == Quantity(100)


async def test_raises_on_overfill(
    mock_uow: AsyncMock,
    mock_event_publisher: AsyncMock,
    mock_order_repository: AsyncMock,
    open_order: Order,
) -> None:
    mock_order_repository.get_by_id.return_value = open_order

    handler = FillOrderHandler(mock_uow, mock_event_publisher)

    with pytest.raises(InvalidOrderFillError):
        await handler.handle(
            FillOrderCommand(order_id=open_order.id.value, fill_quantity=101)
        )

    mock_order_repository.update.assert_not_awaited()
    mock_uow.commit.assert_not_awaited()


async def test_raises_when_order_not_fillable(
    mock_uow: AsyncMock,
    mock_event_publisher: AsyncMock,
    mock_order_repository: AsyncMock,
    new_limit_order: Order,
) -> None:
    mock_order_repository.get_by_id.return_value = new_limit_order

    handler = FillOrderHandler(mock_uow, mock_event_publisher)

    with pytest.raises(InvalidOrderStateError):
        await handler.handle(
            FillOrderCommand(order_id=new_limit_order.id.value, fill_quantity=10)
        )

    mock_order_repository.update.assert_not_awaited()
