from datetime import datetime, timezone

from shared.entity import Entity
from src.exceptions import (
    InvalidOrderFillError,
    InvalidOrderParametersError,
    InvalidOrderStateError,
)
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

_TERMINAL_STATUSES = frozenset(
    {
        OrderStatus.FILLED,
        OrderStatus.CANCELLED,
        OrderStatus.REJECTED,
        OrderStatus.EXPIRED,
    }
)

_CANCELLABLE_STATUSES = frozenset(
    {
        OrderStatus.NEW,
        OrderStatus.OPEN,
        OrderStatus.PARTIALLY_FILLED,
    }
)

_FILLABLE_STATUSES = frozenset(
    {
        OrderStatus.OPEN,
        OrderStatus.PARTIALLY_FILLED,
    }
)


class Order(Entity):
    """Aggregate root representing a trader's order."""

    def __init__(
        self,
        id: OrderId,
        trader_id: TraderId,
        instrument_id: InstrumentId,
        side: OrderSide,
        order_type: OrderType,
        time_in_force: TimeInForce,
        quantity: Quantity,
        filled_quantity: Quantity,
        limit_price: Money | None,
        status: OrderStatus,
        idempotency_key: IdempotencyKey,
        created_at: datetime,
        updated_at: datetime,
    ) -> None:
        self.id = id
        self.trader_id = trader_id
        self.instrument_id = instrument_id
        self.side = side
        self.order_type = order_type
        self.time_in_force = time_in_force
        self.quantity = quantity
        self.filled_quantity = filled_quantity
        self.limit_price = limit_price
        self.status = status
        self.idempotency_key = idempotency_key
        self.created_at = created_at
        self.updated_at = updated_at

        self._status_changed: bool = False
        self._fills_changed: bool = False

    @classmethod
    def create(
        cls,
        trader_id: TraderId,
        instrument_id: InstrumentId,
        side: OrderSide,
        order_type: OrderType,
        time_in_force: TimeInForce,
        quantity: Quantity,
        idempotency_key: IdempotencyKey,
        limit_price: Money | None = None,
    ) -> "Order":
        """Create a new order in NEW status.

        Domain rules:
            - Quantity must be strictly positive.
            - LIMIT orders require a positive limit price.
            - MARKET orders must not carry a limit price.
        """
        if quantity.value == 0:
            raise InvalidOrderParametersError(
                "Order quantity must be greater than zero."
            )

        if order_type is OrderType.LIMIT:
            if limit_price is None:
                raise InvalidOrderParametersError("LIMIT orders require a limit price.")
            if limit_price.amount == 0:
                raise InvalidOrderParametersError(
                    "LIMIT order price must be greater than zero."
                )
        elif order_type is OrderType.MARKET:
            if limit_price is not None:
                raise InvalidOrderParametersError(
                    "MARKET orders must not specify a limit price."
                )

        now = datetime.now(timezone.utc)
        return cls(
            id=OrderId.generate(),
            trader_id=trader_id,
            instrument_id=instrument_id,
            side=side,
            order_type=order_type,
            time_in_force=time_in_force,
            quantity=quantity,
            filled_quantity=Quantity(0),
            limit_price=limit_price,
            status=OrderStatus.NEW,
            idempotency_key=idempotency_key,
            created_at=now,
            updated_at=now,
        )

    @property
    def remaining_quantity(self) -> Quantity:
        """Quantity still available to be filled."""
        return self.quantity - self.filled_quantity

    @property
    def is_terminal(self) -> bool:
        """Whether the order has reached a terminal lifecycle state."""
        return self.status in _TERMINAL_STATUSES

    def open(self) -> None:
        """Accept the order onto the book (NEW → OPEN)."""
        if self.status is not OrderStatus.NEW:
            raise InvalidOrderStateError(
                f"Only NEW orders can be opened; current status is {self.status}."
            )
        self._transition_to(OrderStatus.OPEN)

    def fill(self, fill_quantity: Quantity) -> None:
        """Apply a fill against the remaining quantity.

        Transitions:
            OPEN / PARTIALLY_FILLED → PARTIALLY_FILLED (partial)
            OPEN / PARTIALLY_FILLED → FILLED (complete)
        """
        if self.status not in _FILLABLE_STATUSES:
            raise InvalidOrderStateError(
                f"Order in status {self.status} cannot be filled."
            )

        if fill_quantity.value == 0:
            raise InvalidOrderFillError("Fill quantity must be greater than zero.")

        if fill_quantity > self.remaining_quantity:
            raise InvalidOrderFillError(
                "Fill quantity exceeds remaining order quantity."
            )

        self.filled_quantity = self.filled_quantity + fill_quantity
        self._fills_changed = True
        self.updated_at = datetime.now(timezone.utc)

        if self.remaining_quantity.value == 0:
            self._transition_to(OrderStatus.FILLED)
        else:
            self._transition_to(OrderStatus.PARTIALLY_FILLED)

    def cancel(self) -> None:
        """Cancel an active order."""
        if self.status not in _CANCELLABLE_STATUSES:
            raise InvalidOrderStateError(
                f"Order in status {self.status} cannot be cancelled."
            )
        self._transition_to(OrderStatus.CANCELLED)

    def reject(self) -> None:
        """Reject an order that has not yet been opened."""
        if self.status is not OrderStatus.NEW:
            raise InvalidOrderStateError(
                f"Only NEW orders can be rejected; current status is {self.status}."
            )
        self._transition_to(OrderStatus.REJECTED)

    def expire(self) -> None:
        """Expire an order that is still on the book."""
        if self.status not in {OrderStatus.OPEN, OrderStatus.PARTIALLY_FILLED}:
            raise InvalidOrderStateError(
                f"Order in status {self.status} cannot expire."
            )
        self._transition_to(OrderStatus.EXPIRED)

    def is_status_changed(self) -> bool:
        """Whether the status has been modified since last clear."""
        return self._status_changed

    def is_fills_changed(self) -> bool:
        """Whether filled quantity has been modified since last clear."""
        return self._fills_changed

    def is_changed(self) -> bool:
        """Whether any tracked field has been modified since last clear."""
        return self._status_changed or self._fills_changed

    def clear_changes(self) -> None:
        """Reset change trackers after successful persistence."""
        self._status_changed = False
        self._fills_changed = False

    def _transition_to(self, new_status: OrderStatus) -> None:
        if self.status is new_status:
            return
        self.status = new_status
        self._status_changed = True
        self.updated_at = datetime.now(timezone.utc)
