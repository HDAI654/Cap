from unittest.mock import AsyncMock

from src.application.DTOs import OrderDTO
from src.application.list_orders_by_trader import (
    ListOrdersByTraderHandler,
    ListOrdersByTraderQuery,
)
from src.domain.entities.order import Order
from src.domain.value_objects.trader_id import TraderId


async def test_returns_orders_for_trader(
    mock_uow: AsyncMock,
    mock_order_repository: AsyncMock,
    new_limit_order: Order,
    new_market_order: Order,
    sample_trader_id: TraderId,
) -> None:
    mock_order_repository.list_by_trader.return_value = [
        new_limit_order,
        new_market_order,
    ]

    handler = ListOrdersByTraderHandler(mock_uow)
    result = await handler.handle(
        ListOrdersByTraderQuery(trader_id=sample_trader_id.value)
    )

    assert len(result) == 2
    assert all(isinstance(item, OrderDTO) for item in result)
    assert result[0].order_id == new_limit_order.id.value
    assert result[1].order_id == new_market_order.id.value
    mock_order_repository.list_by_trader.assert_awaited_once()
    mock_uow.commit.assert_not_awaited()


async def test_returns_empty_list_when_no_orders(
    mock_uow: AsyncMock,
    mock_order_repository: AsyncMock,
    sample_trader_id: TraderId,
) -> None:
    mock_order_repository.list_by_trader.return_value = []

    handler = ListOrdersByTraderHandler(mock_uow)
    result = await handler.handle(
        ListOrdersByTraderQuery(trader_id=sample_trader_id.value)
    )

    assert result == []
