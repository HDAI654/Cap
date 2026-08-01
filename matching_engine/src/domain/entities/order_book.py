from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal

from src.domain.entities.resting_order import RestingOrder
from src.domain.entities.trade import Trade
from src.domain.value_objects.instrument_id import InstrumentId
from src.domain.value_objects.money import Money
from src.domain.value_objects.order_id import OrderId
from src.domain.value_objects.order_side import OrderSide
from src.domain.value_objects.order_type import OrderType
from src.domain.value_objects.quantity import Quantity
from src.domain.value_objects.time_in_force import TimeInForce
from src.domain.value_objects.trader_id import TraderId
from src.exceptions import InvalidOrderBookError, OrderNotInBookError


@dataclass(frozen=True, slots=True)
class MatchResult:
    """Outcome of submitting an incoming order to the book."""

    trades: tuple[Trade, ...]
    resting_order: RestingOrder | None
    taker_filled_quantity: int
    taker_remaining_quantity: int
    taker_fully_filled: bool


@dataclass(slots=True)
class _PriceLevel:
    """FIFO queue of resting orders at a single price."""

    price: Money
    orders: deque[RestingOrder] = field(default_factory=deque)

    @property
    def total_quantity(self) -> int:
        return sum(o.remaining_quantity.value for o in self.orders)

    @property
    def is_empty(self) -> bool:
        return not self.orders


class OrderBook:
    """In-memory limit order book for a single instrument.

    Matching rules (price-time priority):
      - Better price first (bids high→low, asks low→high).
      - Same price: FIFO by acceptance sequence.
      - Trade price is the **maker** (resting) price.
      - MARKET orders never rest; unfilled residual is discarded.
      - LIMIT + GTC residual rests; LIMIT + IOC residual is discarded.
      - Self-trade prevention: skip opposite orders from the same trader.

    Data structures (optimized for the hot path):
      - ``_bids`` / ``_asks``: price-amount → deque of orders (O(1) level access).
      - ``_bid_prices`` / ``_ask_prices``: sorted price lists for best-price walks.
      - ``_index``: order_id → (side, price_amount) for O(1) cancel lookup.
    """

    def __init__(self, instrument_id: InstrumentId) -> None:
        self.instrument_id = instrument_id
        self._bids: dict[Decimal, _PriceLevel] = {}
        self._asks: dict[Decimal, _PriceLevel] = {}
        self._bid_prices: list[Decimal] = []  # descending
        self._ask_prices: list[Decimal] = []  # ascending
        self._index: dict[str, tuple[OrderSide, Decimal]] = {}
        self._sequence: int = 0
        self._trade_sequence: int = 0
        self._last_trade_price: Money | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def submit(
        self,
        order_id: OrderId,
        trader_id: TraderId,
        side: OrderSide,
        order_type: OrderType,
        time_in_force: TimeInForce,
        quantity: Quantity,
        limit_price: Money | None,
    ) -> MatchResult:
        """Match an incoming order against the book and optionally rest residual."""
        if quantity.value == 0:
            raise InvalidOrderBookError("Order quantity must be greater than zero.")

        if order_type is OrderType.LIMIT and limit_price is None:
            raise InvalidOrderBookError("LIMIT orders require a limit price.")

        if order_type is OrderType.MARKET and limit_price is not None:
            raise InvalidOrderBookError("MARKET orders must not specify a limit price.")

        if order_id.value in self._index:
            raise InvalidOrderBookError(
                f"Order '{order_id.value}' is already on the book."
            )

        remaining = quantity.value
        trades: list[Trade] = []

        if side is OrderSide.BUY:
            remaining, trades = self._match_buy(
                order_id, trader_id, order_type, limit_price, remaining, trades
            )
        else:
            remaining, trades = self._match_sell(
                order_id, trader_id, order_type, limit_price, remaining, trades
            )

        filled = quantity.value - remaining
        resting: RestingOrder | None = None

        can_rest = (
            remaining > 0
            and order_type is OrderType.LIMIT
            and time_in_force is TimeInForce.GTC
            and limit_price is not None
        )
        if can_rest:
            resting = self._rest(
                order_id=order_id,
                trader_id=trader_id,
                side=side,
                order_type=order_type,
                time_in_force=time_in_force,
                price=limit_price,
                remaining=Quantity(remaining),
            )

        return MatchResult(
            trades=tuple(trades),
            resting_order=resting,
            taker_filled_quantity=filled,
            taker_remaining_quantity=remaining if resting is not None else 0,
            taker_fully_filled=remaining == 0,
        )

    def cancel(self, order_id: OrderId) -> RestingOrder:
        """Remove a resting order from the book."""
        key = order_id.value
        location = self._index.get(key)
        if location is None:
            raise OrderNotInBookError(f"Order '{key}' is not on the book.")

        side, price_amount = location
        levels = self._bids if side is OrderSide.BUY else self._asks
        level = levels.get(price_amount)
        if level is None:
            raise OrderNotInBookError(f"Order '{key}' is not on the book.")

        target: RestingOrder | None = None
        for order in level.orders:
            if order.order_id.value == key:
                target = order
                break

        if target is None:
            raise OrderNotInBookError(f"Order '{key}' is not on the book.")

        level.orders.remove(target)
        del self._index[key]
        if level.is_empty:
            self._remove_level(side, price_amount)

        return target

    def best_bid(self) -> Money | None:
        if not self._bid_prices:
            return None
        return self._bids[self._bid_prices[0]].price

    def best_ask(self) -> Money | None:
        if not self._ask_prices:
            return None
        return self._asks[self._ask_prices[0]].price

    @property
    def last_trade_price(self) -> Money | None:
        return self._last_trade_price

    def depth_bids(self, levels: int = 10) -> list[tuple[Money, int]]:
        result: list[tuple[Money, int]] = []
        for price_amount in self._bid_prices[:levels]:
            level = self._bids[price_amount]
            result.append((level.price, level.total_quantity))
        return result

    def depth_asks(self, levels: int = 10) -> list[tuple[Money, int]]:
        result: list[tuple[Money, int]] = []
        for price_amount in self._ask_prices[:levels]:
            level = self._asks[price_amount]
            result.append((level.price, level.total_quantity))
        return result

    def order_count(self) -> int:
        return len(self._index)

    # ------------------------------------------------------------------
    # Matching
    # ------------------------------------------------------------------

    def _match_buy(
        self,
        taker_id: OrderId,
        taker_trader: TraderId,
        order_type: OrderType,
        limit_price: Money | None,
        remaining: int,
        trades: list[Trade],
    ) -> tuple[int, list[Trade]]:
        while remaining > 0 and self._ask_prices:
            best_price = self._ask_prices[0]
            if order_type is OrderType.LIMIT and limit_price is not None:
                if best_price > limit_price.amount:
                    break

            level = self._asks[best_price]
            remaining = self._consume_level(
                level=level,
                side_of_level=OrderSide.SELL,
                taker_id=taker_id,
                taker_trader=taker_trader,
                taker_side=OrderSide.BUY,
                remaining=remaining,
                trades=trades,
            )
            if level.is_empty:
                self._remove_level(OrderSide.SELL, best_price)
        return remaining, trades

    def _match_sell(
        self,
        taker_id: OrderId,
        taker_trader: TraderId,
        order_type: OrderType,
        limit_price: Money | None,
        remaining: int,
        trades: list[Trade],
    ) -> tuple[int, list[Trade]]:
        while remaining > 0 and self._bid_prices:
            best_price = self._bid_prices[0]
            if order_type is OrderType.LIMIT and limit_price is not None:
                if best_price < limit_price.amount:
                    break

            level = self._bids[best_price]
            remaining = self._consume_level(
                level=level,
                side_of_level=OrderSide.BUY,
                taker_id=taker_id,
                taker_trader=taker_trader,
                taker_side=OrderSide.SELL,
                remaining=remaining,
                trades=trades,
            )
            if level.is_empty:
                self._remove_level(OrderSide.BUY, best_price)
        return remaining, trades

    def _consume_level(
        self,
        level: _PriceLevel,
        side_of_level: OrderSide,
        taker_id: OrderId,
        taker_trader: TraderId,
        taker_side: OrderSide,
        remaining: int,
        trades: list[Trade],
    ) -> int:
        while remaining > 0 and level.orders:
            maker = level.orders[0]

            # Self-trade prevention: skip same-trader resting orders.
            if maker.trader_id == taker_trader:
                level.orders.popleft()
                del self._index[maker.order_id.value]
                continue

            fill_qty = min(remaining, maker.remaining_quantity.value)
            fill = Quantity(fill_qty)

            buyer_id = taker_trader if taker_side is OrderSide.BUY else maker.trader_id
            seller_id = maker.trader_id if taker_side is OrderSide.BUY else taker_trader

            self._trade_sequence += 1
            trade = Trade.create(
                maker_order_id=maker.order_id,
                taker_order_id=taker_id,
                buyer_id=buyer_id,
                seller_id=seller_id,
                instrument_id=self.instrument_id,
                quantity=fill,
                execution_price=maker.price,
                sequence_number=self._trade_sequence,
            )
            trades.append(trade)
            self._last_trade_price = maker.price

            maker.reduce(fill)
            remaining -= fill_qty

            if maker.is_depleted:
                level.orders.popleft()
                del self._index[maker.order_id.value]

        return remaining

    # ------------------------------------------------------------------
    # Rest / index helpers
    # ------------------------------------------------------------------

    def _rest(
        self,
        order_id: OrderId,
        trader_id: TraderId,
        side: OrderSide,
        order_type: OrderType,
        time_in_force: TimeInForce,
        price: Money,
        remaining: Quantity,
    ) -> RestingOrder:
        self._sequence += 1
        resting = RestingOrder(
            order_id=order_id,
            trader_id=trader_id,
            instrument_id=self.instrument_id,
            side=side,
            order_type=order_type,
            time_in_force=time_in_force,
            price=price,
            remaining_quantity=remaining,
            sequence=self._sequence,
            accepted_at=datetime.now(timezone.utc),
        )

        levels = self._bids if side is OrderSide.BUY else self._asks
        prices = self._bid_prices if side is OrderSide.BUY else self._ask_prices
        amount = price.amount

        level = levels.get(amount)
        if level is None:
            level = _PriceLevel(price=price)
            levels[amount] = level
            self._insert_price(prices, amount, descending=(side is OrderSide.BUY))

        level.orders.append(resting)
        self._index[order_id.value] = (side, amount)
        return resting

    def _insert_price(
        self,
        prices: list[Decimal],
        amount: Decimal,
        *,
        descending: bool,
    ) -> None:
        # PERF: binary insertion keeps best-price at index 0.
        lo, hi = 0, len(prices)
        while lo < hi:
            mid = (lo + hi) // 2
            if descending:
                if prices[mid] < amount:
                    hi = mid
                else:
                    lo = mid + 1
            else:
                if prices[mid] > amount:
                    hi = mid
                else:
                    lo = mid + 1
        prices.insert(lo, amount)

    def _remove_level(self, side: OrderSide, price_amount: Decimal) -> None:
        if side is OrderSide.BUY:
            self._bids.pop(price_amount, None)
            try:
                self._bid_prices.remove(price_amount)
            except ValueError:
                pass
        else:
            self._asks.pop(price_amount, None)
            try:
                self._ask_prices.remove(price_amount)
            except ValueError:
                pass
