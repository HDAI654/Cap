from decimal import Decimal

import pytest

from src.domain.entities.order_book import OrderBook
from src.domain.value_objects.currency import Currency
from src.domain.value_objects.instrument_id import InstrumentId
from src.domain.value_objects.money import Money
from src.domain.value_objects.order_id import OrderId
from src.domain.value_objects.order_side import OrderSide
from src.domain.value_objects.order_type import OrderType
from src.domain.value_objects.quantity import Quantity
from src.domain.value_objects.time_in_force import TimeInForce
from src.domain.value_objects.trader_id import TraderId
from src.exceptions import InvalidOrderBookError, OrderNotInBookError


def _usd(amount: str | int) -> Money:
    return Money(Decimal(str(amount)), Currency.USD)


def _book() -> OrderBook:
    return OrderBook(InstrumentId.generate())


def _submit(
    book: OrderBook,
    *,
    side: OrderSide,
    qty: int,
    price: Money | None,
    order_type: OrderType = OrderType.LIMIT,
    tif: TimeInForce = TimeInForce.GTC,
    trader: TraderId | None = None,
    order_id: OrderId | None = None,
):
    return book.submit(
        order_id=order_id or OrderId.generate(),
        trader_id=trader or TraderId.generate(),
        side=side,
        order_type=order_type,
        time_in_force=tif,
        quantity=Quantity(qty),
        limit_price=price,
    )


# ---------------------------------------------------------------------------
# Resting
# ---------------------------------------------------------------------------


def test_limit_buy_rests_on_empty_book() -> None:
    book = _book()
    result = _submit(book, side=OrderSide.BUY, qty=10, price=_usd("100"))

    assert result.trades == ()
    assert result.resting_order is not None
    assert result.resting_order.remaining_quantity.value == 10
    assert book.best_bid() == _usd("100")
    assert book.best_ask() is None
    assert book.order_count() == 1


def test_limit_sell_rests_on_empty_book() -> None:
    book = _book()
    result = _submit(book, side=OrderSide.SELL, qty=5, price=_usd("50.25"))

    assert result.resting_order is not None
    assert book.best_ask() == _usd("50.25")
    assert book.best_bid() is None


# ---------------------------------------------------------------------------
# Matching
# ---------------------------------------------------------------------------


def test_full_match_buy_against_resting_sell() -> None:
    book = _book()
    seller = TraderId.generate()
    buyer = TraderId.generate()
    sell_id = OrderId.generate()

    _submit(
        book,
        side=OrderSide.SELL,
        qty=10,
        price=_usd("10.00"),
        trader=seller,
        order_id=sell_id,
    )
    result = _submit(
        book,
        side=OrderSide.BUY,
        qty=10,
        price=_usd("10.00"),
        trader=buyer,
    )

    assert len(result.trades) == 1
    trade = result.trades[0]
    assert trade.quantity.value == 10
    assert trade.execution_price == _usd("10.00")
    assert trade.maker_order_id == sell_id
    assert trade.buyer_id == buyer
    assert trade.seller_id == seller
    assert result.taker_fully_filled is True
    assert result.resting_order is None
    assert book.order_count() == 0
    assert book.last_trade_price == _usd("10.00")


def test_partial_match_leaves_residual_on_book() -> None:
    book = _book()
    _submit(book, side=OrderSide.SELL, qty=10, price=_usd("20.00"))
    result = _submit(book, side=OrderSide.BUY, qty=4, price=_usd("20.00"))

    assert result.taker_filled_quantity == 4
    assert result.taker_fully_filled is True
    assert result.resting_order is None
    assert book.order_count() == 1
    assert book.depth_asks()[0][1] == 6


def test_aggressive_buy_walks_multiple_ask_levels() -> None:
    book = _book()
    _submit(book, side=OrderSide.SELL, qty=5, price=_usd("10.00"))
    _submit(book, side=OrderSide.SELL, qty=5, price=_usd("11.00"))
    result = _submit(book, side=OrderSide.BUY, qty=8, price=_usd("11.00"))

    assert result.taker_filled_quantity == 8
    assert len(result.trades) == 2
    assert result.trades[0].execution_price == _usd("10.00")
    assert result.trades[1].execution_price == _usd("11.00")
    assert book.depth_asks()[0][1] == 2


def test_price_time_priority_fifo_at_same_level() -> None:
    book = _book()
    first = OrderId.generate()
    second = OrderId.generate()
    _submit(book, side=OrderSide.SELL, qty=3, price=_usd("5.00"), order_id=first)
    _submit(book, side=OrderSide.SELL, qty=3, price=_usd("5.00"), order_id=second)
    result = _submit(book, side=OrderSide.BUY, qty=3, price=_usd("5.00"))

    assert result.trades[0].maker_order_id == first


def test_limit_does_not_cross_worse_price() -> None:
    book = _book()
    _submit(book, side=OrderSide.SELL, qty=10, price=_usd("15.00"))
    result = _submit(book, side=OrderSide.BUY, qty=10, price=_usd("14.00"))

    assert result.trades == ()
    assert result.resting_order is not None
    assert book.order_count() == 2


# ---------------------------------------------------------------------------
# MARKET / IOC
# ---------------------------------------------------------------------------


def test_market_buy_fills_and_does_not_rest() -> None:
    book = _book()
    _submit(book, side=OrderSide.SELL, qty=5, price=_usd("9.00"))
    result = _submit(
        book,
        side=OrderSide.BUY,
        qty=10,
        price=None,
        order_type=OrderType.MARKET,
        tif=TimeInForce.IOC,
    )

    assert result.taker_filled_quantity == 5
    assert result.resting_order is None
    assert result.taker_remaining_quantity == 0
    assert book.order_count() == 0


def test_ioc_limit_discards_unfilled_residual() -> None:
    book = _book()
    _submit(book, side=OrderSide.SELL, qty=3, price=_usd("10.00"))
    result = _submit(
        book,
        side=OrderSide.BUY,
        qty=10,
        price=_usd("10.00"),
        tif=TimeInForce.IOC,
    )

    assert result.taker_filled_quantity == 3
    assert result.resting_order is None
    assert book.order_count() == 0


# ---------------------------------------------------------------------------
# Cancel
# ---------------------------------------------------------------------------


def test_cancel_removes_resting_order() -> None:
    book = _book()
    oid = OrderId.generate()
    _submit(book, side=OrderSide.BUY, qty=7, price=_usd("1.00"), order_id=oid)

    removed = book.cancel(oid)

    assert removed.order_id == oid
    assert book.order_count() == 0
    assert book.best_bid() is None


def test_cancel_missing_raises() -> None:
    book = _book()
    with pytest.raises(OrderNotInBookError):
        book.cancel(OrderId.generate())


# ---------------------------------------------------------------------------
# Self-trade prevention
# ---------------------------------------------------------------------------


def test_self_trade_is_skipped() -> None:
    book = _book()
    trader = TraderId.generate()
    _submit(book, side=OrderSide.SELL, qty=5, price=_usd("10.00"), trader=trader)
    result = _submit(
        book, side=OrderSide.BUY, qty=5, price=_usd("10.00"), trader=trader
    )

    assert result.trades == ()
    # Resting sell was skipped and removed; buy rests.
    assert result.resting_order is not None
    assert book.best_ask() is None
    assert book.best_bid() == _usd("10.00")


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def test_market_with_price_raises() -> None:
    book = _book()
    with pytest.raises(InvalidOrderBookError):
        _submit(
            book,
            side=OrderSide.BUY,
            qty=1,
            price=_usd("1.00"),
            order_type=OrderType.MARKET,
        )


def test_limit_without_price_raises() -> None:
    book = _book()
    with pytest.raises(InvalidOrderBookError):
        _submit(
            book,
            side=OrderSide.BUY,
            qty=1,
            price=None,
            order_type=OrderType.LIMIT,
        )


def test_duplicate_order_id_raises() -> None:
    book = _book()
    oid = OrderId.generate()
    _submit(book, side=OrderSide.BUY, qty=1, price=_usd("1.00"), order_id=oid)
    with pytest.raises(InvalidOrderBookError):
        _submit(book, side=OrderSide.BUY, qty=1, price=_usd("1.00"), order_id=oid)
