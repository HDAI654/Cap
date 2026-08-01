from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from src.application.submit_order import (
    SubmitOrderCommand,
    SubmitOrderHandler,
    SubmitOrderResult,
)
from src.domain.entities.order import Order
from src.domain.events.order_events import OrderSubmitted
from src.domain.value_objects.instrument_id import InstrumentId
from src.domain.value_objects.order_status import OrderStatus
from src.domain.value_objects.order_type import OrderType
from src.domain.value_objects.trader_id import TraderId
from src.exceptions import InvalidOrderParametersError, OrderAlreadyExistsError


async def test_submits_limit_order(
    mock_uow: AsyncMock,
    mock_event_publisher: AsyncMock,
    mock_order_repository: AsyncMock,
    sample_trader_id: TraderId,
    sample_instrument_id: InstrumentId,
) -> None:
    mock_order_repository.get_by_idempotency_key.return_value = None

    handler = SubmitOrderHandler(mock_uow, mock_event_publisher)
    result = await handler.handle(
        SubmitOrderCommand(
            trader_id=sample_trader_id.value,
            instrument_id=sample_instrument_id.value,
            side="BUY",
            order_type="LIMIT",
            time_in_force="GTC",
            quantity=100,
            idempotency_key="submit-limit-001",
            limit_price=Decimal("10.50"),
            limit_price_currency="USD",
        )
    )

    assert isinstance(result, SubmitOrderResult)
    assert result.order_id

    mock_order_repository.get_by_idempotency_key.assert_awaited_once()
    mock_order_repository.add.assert_awaited_once()
    added: Order = mock_order_repository.add.await_args.args[0]
    assert added.trader_id == sample_trader_id
    assert added.instrument_id == sample_instrument_id
    assert added.order_type is OrderType.LIMIT
    assert added.status is OrderStatus.NEW
    assert added.quantity.value == 100
    assert added.limit_price is not None
    assert added.limit_price.amount == Decimal("10.50")
    mock_uow.commit.assert_awaited_once()
    mock_event_publisher.publish.assert_awaited_once()
    event = mock_event_publisher.publish.await_args.args[0]
    assert isinstance(event, OrderSubmitted)
    assert event.order_id == result.order_id
    assert event.side == "BUY"
    assert event.order_type == "LIMIT"
    assert event.quantity == 100
    assert event.limit_price == Decimal("10.50")


async def test_submits_market_order(
    mock_uow: AsyncMock,
    mock_event_publisher: AsyncMock,
    mock_order_repository: AsyncMock,
    sample_trader_id: TraderId,
    sample_instrument_id: InstrumentId,
) -> None:
    mock_order_repository.get_by_idempotency_key.return_value = None

    handler = SubmitOrderHandler(mock_uow, mock_event_publisher)
    result = await handler.handle(
        SubmitOrderCommand(
            trader_id=sample_trader_id.value,
            instrument_id=sample_instrument_id.value,
            side="SELL",
            order_type="MARKET",
            time_in_force="IOC",
            quantity=50,
            idempotency_key="submit-market-001",
        )
    )

    assert isinstance(result, SubmitOrderResult)
    added: Order = mock_order_repository.add.await_args.args[0]
    assert added.order_type is OrderType.MARKET
    assert added.limit_price is None
    mock_uow.commit.assert_awaited_once()
    mock_event_publisher.publish.assert_awaited_once()
    event = mock_event_publisher.publish.await_args.args[0]
    assert isinstance(event, OrderSubmitted)
    assert event.order_type == "MARKET"
    assert event.limit_price is None


async def test_raises_when_idempotency_key_exists(
    mock_uow: AsyncMock,
    mock_event_publisher: AsyncMock,
    mock_order_repository: AsyncMock,
    new_limit_order: Order,
    sample_trader_id: TraderId,
    sample_instrument_id: InstrumentId,
) -> None:
    mock_order_repository.get_by_idempotency_key.return_value = new_limit_order

    handler = SubmitOrderHandler(mock_uow, mock_event_publisher)

    with pytest.raises(OrderAlreadyExistsError):
        await handler.handle(
            SubmitOrderCommand(
                trader_id=sample_trader_id.value,
                instrument_id=sample_instrument_id.value,
                side="BUY",
                order_type="LIMIT",
                time_in_force="GTC",
                quantity=100,
                idempotency_key="limit-key-001",
                limit_price=Decimal("10.50"),
                limit_price_currency="USD",
            )
        )

    mock_order_repository.add.assert_not_awaited()
    mock_uow.commit.assert_not_awaited()
    mock_event_publisher.publish.assert_not_awaited()


async def test_rejects_invalid_side(
    mock_uow: AsyncMock,
    mock_event_publisher: AsyncMock,
    mock_order_repository: AsyncMock,
    sample_trader_id: TraderId,
    sample_instrument_id: InstrumentId,
) -> None:
    handler = SubmitOrderHandler(mock_uow, mock_event_publisher)

    with pytest.raises(InvalidOrderParametersError):
        await handler.handle(
            SubmitOrderCommand(
                trader_id=sample_trader_id.value,
                instrument_id=sample_instrument_id.value,
                side="HOLD",
                order_type="LIMIT",
                time_in_force="GTC",
                quantity=10,
                idempotency_key="bad-side",
                limit_price=Decimal("1.00"),
                limit_price_currency="USD",
            )
        )

    mock_order_repository.get_by_idempotency_key.assert_not_awaited()
    mock_uow.commit.assert_not_awaited()


async def test_rejects_invalid_order_type(
    mock_uow: AsyncMock,
    mock_event_publisher: AsyncMock,
    mock_order_repository: AsyncMock,
    sample_trader_id: TraderId,
    sample_instrument_id: InstrumentId,
) -> None:
    handler = SubmitOrderHandler(mock_uow, mock_event_publisher)

    with pytest.raises(InvalidOrderParametersError):
        await handler.handle(
            SubmitOrderCommand(
                trader_id=sample_trader_id.value,
                instrument_id=sample_instrument_id.value,
                side="BUY",
                order_type="STOP",
                time_in_force="GTC",
                quantity=10,
                idempotency_key="bad-type",
            )
        )


async def test_rejects_invalid_time_in_force(
    mock_uow: AsyncMock,
    mock_event_publisher: AsyncMock,
    mock_order_repository: AsyncMock,
    sample_trader_id: TraderId,
    sample_instrument_id: InstrumentId,
) -> None:
    handler = SubmitOrderHandler(mock_uow, mock_event_publisher)

    with pytest.raises(InvalidOrderParametersError):
        await handler.handle(
            SubmitOrderCommand(
                trader_id=sample_trader_id.value,
                instrument_id=sample_instrument_id.value,
                side="BUY",
                order_type="MARKET",
                time_in_force="GTD",
                quantity=10,
                idempotency_key="bad-tif",
            )
        )


async def test_rejects_invalid_limit_price_currency(
    mock_uow: AsyncMock,
    mock_event_publisher: AsyncMock,
    mock_order_repository: AsyncMock,
    sample_trader_id: TraderId,
    sample_instrument_id: InstrumentId,
) -> None:
    handler = SubmitOrderHandler(mock_uow, mock_event_publisher)

    with pytest.raises(InvalidOrderParametersError):
        await handler.handle(
            SubmitOrderCommand(
                trader_id=sample_trader_id.value,
                instrument_id=sample_instrument_id.value,
                side="BUY",
                order_type="LIMIT",
                time_in_force="GTC",
                quantity=10,
                idempotency_key="bad-ccy",
                limit_price=Decimal("1.00"),
                limit_price_currency="XYZ",
            )
        )
