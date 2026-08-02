from datetime import datetime, timezone

from shared.entity import Entity
from src.domain.value_objects.currency import Currency
from src.domain.value_objects.instrument_id import InstrumentId
from src.domain.value_objects.instrument_status import InstrumentStatus
from src.domain.value_objects.money import Money
from src.domain.value_objects.quantity import Quantity
from src.exceptions import InvalidInstrumentParametersError, InvalidInstrumentStateError


class Instrument(Entity):
    """Aggregate root for a tradable instrument."""

    def __init__(
        self,
        id: InstrumentId,
        symbol: str,
        name: str,
        tick_size: Money,
        lot_size: Quantity,
        minimum_order_quantity: Quantity,
        maximum_order_quantity: Quantity,
        currency: Currency,
        total_shares: Quantity,
        status: InstrumentStatus,
        created_at: datetime,
        updated_at: datetime,
    ) -> None:
        self.id = id
        self.symbol = symbol
        self.name = name
        self.tick_size = tick_size
        self.lot_size = lot_size
        self.minimum_order_quantity = minimum_order_quantity
        self.maximum_order_quantity = maximum_order_quantity
        self.currency = currency
        self.total_shares = total_shares
        self.status = status
        self.created_at = created_at
        self.updated_at = updated_at
        self._status_changed = False
        self._shares_changed = False

    @classmethod
    def create(
        cls,
        symbol: str,
        name: str,
        tick_size: Money,
        lot_size: Quantity,
        minimum_order_quantity: Quantity,
        maximum_order_quantity: Quantity,
        currency: Currency,
        total_shares: Quantity | None = None,
    ) -> "Instrument":
        """Create a new instrument in PENDING status."""
        symbol = symbol.strip().upper()
        name = name.strip()
        if not symbol:
            raise InvalidInstrumentParametersError("Symbol is required.")
        if not name:
            raise InvalidInstrumentParametersError("Name is required.")
        if tick_size.amount == 0:
            raise InvalidInstrumentParametersError(
                "Tick size must be greater than zero."
            )
        if tick_size.currency is not currency:
            raise InvalidInstrumentParametersError(
                "Tick size currency must match instrument currency."
            )
        if lot_size.value == 0:
            raise InvalidInstrumentParametersError(
                "Lot size must be greater than zero."
            )
        if minimum_order_quantity.value == 0:
            raise InvalidInstrumentParametersError(
                "Minimum order quantity must be greater than zero."
            )
        if maximum_order_quantity.value < minimum_order_quantity.value:
            raise InvalidInstrumentParametersError(
                "Maximum order quantity must be >= minimum order quantity."
            )
        shares = total_shares if total_shares is not None else Quantity(0)
        now = datetime.now(timezone.utc)
        return cls(
            id=InstrumentId.generate(),
            symbol=symbol,
            name=name,
            tick_size=tick_size,
            lot_size=lot_size,
            minimum_order_quantity=minimum_order_quantity,
            maximum_order_quantity=maximum_order_quantity,
            currency=currency,
            total_shares=shares,
            status=InstrumentStatus.PENDING,
            created_at=now,
            updated_at=now,
        )

    def activate(self) -> None:
        if self.status is InstrumentStatus.DELISTED:
            raise InvalidInstrumentStateError("Cannot activate a delisted instrument.")
        if self.status is InstrumentStatus.ACTIVE:
            raise InvalidInstrumentStateError("Instrument is already active.")
        self.status = InstrumentStatus.ACTIVE
        self._status_changed = True
        self._touch()

    def halt(self) -> None:
        if self.status is not InstrumentStatus.ACTIVE:
            raise InvalidInstrumentStateError("Only ACTIVE instruments can be halted.")
        self.status = InstrumentStatus.HALTED
        self._status_changed = True
        self._touch()

    def delist(self) -> None:
        if self.status is InstrumentStatus.DELISTED:
            raise InvalidInstrumentStateError("Instrument is already delisted.")
        self.status = InstrumentStatus.DELISTED
        self._status_changed = True
        self._touch()

    def allocate_shares(self, quantity: Quantity) -> None:
        """Increase total share supply (primary allocation)."""
        if quantity.value == 0:
            raise InvalidInstrumentParametersError(
                "Allocation quantity must be greater than zero."
            )
        if self.status is InstrumentStatus.DELISTED:
            raise InvalidInstrumentStateError(
                "Cannot allocate shares to a delisted instrument."
            )
        self.total_shares = self.total_shares + quantity
        self._shares_changed = True
        self._touch()

    def is_status_changed(self) -> bool:
        return self._status_changed

    def is_shares_changed(self) -> bool:
        return self._shares_changed

    def is_changed(self) -> bool:
        return self._status_changed or self._shares_changed

    def clear_changes(self) -> None:
        self._status_changed = False
        self._shares_changed = False

    def _touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc)
