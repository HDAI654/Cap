from datetime import datetime, timezone

import pytest

from src.domain.entities.order import Order
from src.domain.value_objects.currency import Currency
from src.domain.value_objects.idempotency_key import IdempotencyKey
from src.domain.value_objects.instrument_id import InstrumentId
from src.domain.value_objects.money import Money
from src.domain.value_objects.order_id import OrderId
from src.domain.value_objects.order_side import OrderSide
from src.domain.value_objects.order_status import OrderStatus
from src.domain.value_objects.order_type import OrderType
from src.domain.value_objects.quantity import Quantity
from src.domain.value_objects.time_in_force import TimeInForce
from src.domain.value_objects.trader_id import TraderId
from src.exceptions import (
    InvalidOrderFillError,
    InvalidOrderParametersError,
    InvalidOrderStateError,
)


def _create_limit_order(
    quantity: int = 100,
    price: str = "10.50",
    side: OrderSide = OrderSide.BUY,
    tif: TimeInForce = TimeInForce.GTC,
    key: str = "key-001",
) -> Order:
    return Order.create(
        trader_id=TraderId.generate(),
        instrument_id=InstrumentId.generate(),
        side=side,
        order_type=OrderType.LIMIT,
        time_in_force=tif,
        quantity=Quantity(quantity),
        idempotency_key=IdempotencyKey(key),
        limit_price=Money(price, Currency.USD),
    )


def _create_market_order(
    quantity: int = 50,
    side: OrderSide = OrderSide.SELL,
    tif: TimeInForce = TimeInForce.IOC,
    key: str = "mkt-001",
) -> Order:
    return Order.create(
        trader_id=TraderId.generate(),
        instrument_id=InstrumentId.generate(),
        side=side,
        order_type=OrderType.MARKET,
        time_in_force=tif,
        quantity=Quantity(quantity),
        idempotency_key=IdempotencyKey(key),
    )


class TestOrderCreate:
    def test_create_limit_order(self):
        trader_id = TraderId.generate()
        instrument_id = InstrumentId.generate()
        key = IdempotencyKey("client-001")
        price = Money("25.50", Currency.USD)

        order = Order.create(
            trader_id=trader_id,
            instrument_id=instrument_id,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            quantity=Quantity(100),
            idempotency_key=key,
            limit_price=price,
        )

        assert isinstance(order.id, OrderId)
        assert order.trader_id == trader_id
        assert order.instrument_id == instrument_id
        assert order.side is OrderSide.BUY
        assert order.order_type is OrderType.LIMIT
        assert order.time_in_force is TimeInForce.GTC
        assert order.quantity == Quantity(100)
        assert order.filled_quantity == Quantity(0)
        assert order.remaining_quantity == Quantity(100)
        assert order.limit_price == price
        assert order.status is OrderStatus.NEW
        assert order.idempotency_key == key
        assert isinstance(order.created_at, datetime)
        assert isinstance(order.updated_at, datetime)
        assert order.created_at.tzinfo is timezone.utc
        assert not order.is_terminal
        assert not order.is_status_changed()
        assert not order.is_fills_changed()
        assert not order.is_changed()

    def test_create_market_order(self):
        order = _create_market_order()

        assert order.order_type is OrderType.MARKET
        assert order.limit_price is None
        assert order.status is OrderStatus.NEW
        assert order.filled_quantity == Quantity(0)

    def test_create_rejects_zero_quantity(self):
        with pytest.raises(InvalidOrderParametersError):
            Order.create(
                trader_id=TraderId.generate(),
                instrument_id=InstrumentId.generate(),
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                time_in_force=TimeInForce.GTC,
                quantity=Quantity(0),
                idempotency_key=IdempotencyKey("z"),
                limit_price=Money("1.00", Currency.USD),
            )

    def test_create_limit_requires_price(self):
        with pytest.raises(InvalidOrderParametersError):
            Order.create(
                trader_id=TraderId.generate(),
                instrument_id=InstrumentId.generate(),
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                time_in_force=TimeInForce.GTC,
                quantity=Quantity(10),
                idempotency_key=IdempotencyKey("no-price"),
                limit_price=None,
            )

    def test_create_limit_rejects_zero_price(self):
        with pytest.raises(InvalidOrderParametersError):
            Order.create(
                trader_id=TraderId.generate(),
                instrument_id=InstrumentId.generate(),
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                time_in_force=TimeInForce.GTC,
                quantity=Quantity(10),
                idempotency_key=IdempotencyKey("zero-price"),
                limit_price=Money("0.00", Currency.USD),
            )

    def test_create_market_rejects_price(self):
        with pytest.raises(InvalidOrderParametersError):
            Order.create(
                trader_id=TraderId.generate(),
                instrument_id=InstrumentId.generate(),
                side=OrderSide.SELL,
                order_type=OrderType.MARKET,
                time_in_force=TimeInForce.IOC,
                quantity=Quantity(10),
                idempotency_key=IdempotencyKey("mkt-price"),
                limit_price=Money("1.00", Currency.USD),
            )


class TestOrderOpen:
    def test_open_from_new(self):
        order = _create_limit_order()
        order.open()

        assert order.status is OrderStatus.OPEN
        assert order.is_status_changed()
        assert order.is_changed()

    def test_open_from_non_new_raises(self):
        order = _create_limit_order()
        order.open()

        with pytest.raises(InvalidOrderStateError):
            order.open()


class TestOrderFill:
    def test_partial_fill(self):
        order = _create_limit_order(quantity=100)
        order.open()
        order.clear_changes()

        order.fill(Quantity(40))

        assert order.filled_quantity == Quantity(40)
        assert order.remaining_quantity == Quantity(60)
        assert order.status is OrderStatus.PARTIALLY_FILLED
        assert order.is_fills_changed()
        assert order.is_status_changed()
        assert not order.is_terminal

    def test_full_fill_from_open(self):
        order = _create_limit_order(quantity=100)
        order.open()

        order.fill(Quantity(100))

        assert order.filled_quantity == Quantity(100)
        assert order.remaining_quantity == Quantity(0)
        assert order.status is OrderStatus.FILLED
        assert order.is_terminal

    def test_full_fill_after_partial(self):
        order = _create_limit_order(quantity=100)
        order.open()
        order.fill(Quantity(30))
        order.fill(Quantity(70))

        assert order.status is OrderStatus.FILLED
        assert order.filled_quantity == Quantity(100)
        assert order.is_terminal

    def test_fill_zero_quantity_raises(self):
        order = _create_limit_order()
        order.open()

        with pytest.raises(InvalidOrderFillError):
            order.fill(Quantity(0))

    def test_fill_exceeds_remaining_raises(self):
        order = _create_limit_order(quantity=10)
        order.open()

        with pytest.raises(InvalidOrderFillError):
            order.fill(Quantity(11))

    def test_fill_from_new_raises(self):
        order = _create_limit_order()

        with pytest.raises(InvalidOrderStateError):
            order.fill(Quantity(1))

    def test_fill_from_filled_raises(self):
        order = _create_limit_order(quantity=10)
        order.open()
        order.fill(Quantity(10))

        with pytest.raises(InvalidOrderStateError):
            order.fill(Quantity(1))

    def test_fill_from_cancelled_raises(self):
        order = _create_limit_order()
        order.open()
        order.cancel()

        with pytest.raises(InvalidOrderStateError):
            order.fill(Quantity(1))


class TestOrderCancel:
    def test_cancel_from_new(self):
        order = _create_limit_order()
        order.cancel()

        assert order.status is OrderStatus.CANCELLED
        assert order.is_terminal
        assert order.is_status_changed()

    def test_cancel_from_open(self):
        order = _create_limit_order()
        order.open()
        order.cancel()

        assert order.status is OrderStatus.CANCELLED
        assert order.is_terminal

    def test_cancel_from_partially_filled(self):
        order = _create_limit_order(quantity=100)
        order.open()
        order.fill(Quantity(25))
        order.cancel()

        assert order.status is OrderStatus.CANCELLED
        assert order.filled_quantity == Quantity(25)
        assert order.is_terminal

    def test_cancel_from_filled_raises(self):
        order = _create_limit_order(quantity=10)
        order.open()
        order.fill(Quantity(10))

        with pytest.raises(InvalidOrderStateError):
            order.cancel()

    def test_cancel_from_rejected_raises(self):
        order = _create_limit_order()
        order.reject()

        with pytest.raises(InvalidOrderStateError):
            order.cancel()


class TestOrderReject:
    def test_reject_from_new(self):
        order = _create_limit_order()
        order.reject()

        assert order.status is OrderStatus.REJECTED
        assert order.is_terminal

    def test_reject_from_open_raises(self):
        order = _create_limit_order()
        order.open()

        with pytest.raises(InvalidOrderStateError):
            order.reject()


class TestOrderExpire:
    def test_expire_from_open(self):
        order = _create_limit_order()
        order.open()
        order.expire()

        assert order.status is OrderStatus.EXPIRED
        assert order.is_terminal

    def test_expire_from_partially_filled(self):
        order = _create_limit_order(quantity=100)
        order.open()
        order.fill(Quantity(20))
        order.expire()

        assert order.status is OrderStatus.EXPIRED
        assert order.filled_quantity == Quantity(20)
        assert order.is_terminal

    def test_expire_from_new_raises(self):
        order = _create_limit_order()

        with pytest.raises(InvalidOrderStateError):
            order.expire()

    def test_expire_from_filled_raises(self):
        order = _create_limit_order(quantity=5)
        order.open()
        order.fill(Quantity(5))

        with pytest.raises(InvalidOrderStateError):
            order.expire()


class TestOrderChangeTrackers:
    def test_clear_changes(self):
        order = _create_limit_order()
        order.open()
        order.fill(Quantity(10))

        assert order.is_changed()
        order.clear_changes()
        assert not order.is_status_changed()
        assert not order.is_fills_changed()
        assert not order.is_changed()

    def test_status_only_change(self):
        order = _create_limit_order()
        order.open()

        assert order.is_status_changed()
        assert not order.is_fills_changed()

    def test_fill_marks_both_when_status_changes(self):
        order = _create_limit_order(quantity=50)
        order.open()
        order.clear_changes()
        order.fill(Quantity(50))

        assert order.is_fills_changed()
        assert order.is_status_changed()
