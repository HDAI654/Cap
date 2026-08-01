from decimal import Decimal
from unittest.mock import AsyncMock

from src.application.DTOs import OrderDTO
from src.application.get_order import GetOrderHandler, GetOrderQuery
from src.domain.entities.order import Order
from src.domain.value_objects.order_status import OrderStatus


async def test_returns_order_dto(
    mock_uow: AsyncMock,
    mock_order_repository: AsyncMock,
    new_limit_order: Order,
) -> None:
    mock_order_repository.get_by_id.return_value = new_limit_order

    handler = GetOrderHandler(mock_uow)
    result = await handler.handle(
        GetOrderQuery(order_id=new_limit_order.id.value)
    )

    assert isinstance(result, OrderDTO)
    assert result.order_id == new_limit_order.id.value
    assert result.trader_id == new_limit_order.trader_id.value
    assert result.instrument_id == new_limit_order.instrument_id.value
    assert result.side == "BUY"
    assert result.order_type == "LIMIT"
    assert result.time_in_force == "GTC"
    assert result.quantity == 100
    assert result.filled_quantity == 0
    assert result.remaining_quantity == 100
    assert result.limit_price == Decimal("10.50")
    assert result.limit_price_currency == "USD"
    assert result.status == OrderStatus.NEW.value
    assert result.idempotency_key == "limit-key-001"
    mock_uow.commit.assert_not_awaited()


async def test_returns_market_order_without_price(
    mock_uow: AsyncMock,
    mock_order_repository: AsyncMock,
    new_market_order: Order,
) -> None:
    mock_order_repository.get_by_id.return_value = new_market_order

    handler = GetOrderHandler(mock_uow)
    result = await handler.handle(
        GetOrderQuery(order_id=new_market_order.id.value)
    )

    assert result.order_type == "MARKET"
    assert result.limit_price is None
    assert result.limit_price_currency is None
    assert result.quantity == 50
