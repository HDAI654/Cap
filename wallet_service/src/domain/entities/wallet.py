from shared.entity import Entity
from src.exceptions import CashBalanceNotFoundError, HoldingNotFoundError
from src.domain.entities.cash_balance import CashBalance
from src.domain.entities.holding import Holding
from src.domain.value_objects.wallet_status import WalletStatus
from src.domain.value_objects.currency import Currency
from src.domain.value_objects.instrument_id import InstrumentId
from src.domain.value_objects.money import Money
from src.domain.value_objects.quantity import Quantity
from src.domain.value_objects.trader_id import TraderId
from src.domain.value_objects.wallet_id import WalletId


class Wallet(Entity):
    """Aggregate root representing a trader's wallet."""

    def __init__(
        self,
        id: WalletId,
        trader_id: TraderId,
        status: WalletStatus,
        cash_balances: list[CashBalance] | None = None,
        holdings: list[Holding] | None = None,
    ) -> None:
        self.id: WalletId = id
        self.trader_id: TraderId = trader_id
        self.status: WalletStatus = status

        # Change trackers
        self._status_changed: bool = False
        self._created_cash: set[Currency] = set()
        self._updated_cash: set[Currency] = set()
        self._created_holdings: set[InstrumentId] = set()
        self._updated_holdings: set[InstrumentId] = set()
        self._removed_holdings: set[InstrumentId] = set()

        self._cash_balances: dict[Currency, CashBalance] = {
            b.currency: b for b in (cash_balances or [])
        }
        self._holdings: dict[InstrumentId, Holding] = {
            h.instrument_id: h for h in (holdings or [])
        }

    @classmethod
    def create(cls, trader_id: TraderId) -> "Wallet":
        """Create a new wallet."""
        return cls(
            id=WalletId.generate(),
            trader_id=trader_id,
            status=WalletStatus.ACTIVE,
        )

    @property
    def cash_balances(self) -> tuple[CashBalance, ...]:
        """Return the wallet cash balances."""
        return tuple(self._cash_balances.values())

    @property
    def holdings(self) -> tuple[Holding, ...]:
        """Return the wallet holdings."""
        return tuple(self._holdings.values())

    def deposit_cash(self, amount: Money) -> None:
        """Deposit cash into the wallet."""
        balance = self._get_cash_balance(amount.currency)

        if balance is None:
            balance = CashBalance(
                currency=amount.currency,
                available=Money(0, amount.currency),
                reserved=Money(0, amount.currency),
            )
            self._cash_balances[amount.currency] = balance
            self._mark_cash_created(amount.currency)
        else:
            self._mark_cash_updated(amount.currency)

        balance.deposit(amount)

    def withdraw_cash(self, amount: Money) -> None:
        """Withdraw cash from the wallet."""
        self._require_cash_balance(amount.currency).withdraw(amount)
        self._mark_cash_updated(amount.currency)

    def reserve_cash(self, amount: Money) -> None:
        """Reserve cash for an order."""
        self._require_cash_balance(amount.currency).reserve(amount)
        self._mark_cash_updated(amount.currency)

    def release_cash(self, amount: Money) -> None:
        """Release reserved cash."""
        self._require_cash_balance(amount.currency).release(amount)
        self._mark_cash_updated(amount.currency)

    def consume_reserved_cash(self, amount: Money) -> None:
        """Consume reserved cash after settlement."""
        self._require_cash_balance(amount.currency).consume_reserved(amount)
        self._mark_cash_updated(amount.currency)

    def add_holding(
        self,
        instrument_id: InstrumentId,
        quantity: Quantity,
        average_cost: Money,
    ) -> None:
        """Add shares to a holding."""
        holding = self._get_holding(instrument_id)

        if holding is None:
            holding = Holding(
                instrument_id=instrument_id,
                available=Quantity(0),
                reserved=Quantity(0),
                average_cost=average_cost,
            )
            self._holdings[instrument_id] = holding
            self._mark_holding_created(instrument_id)
        else:
            self._mark_holding_updated(instrument_id)

        holding.add(quantity)
        holding.update_average_cost(average_cost)

    def remove_holding(
        self,
        instrument_id: InstrumentId,
        quantity: Quantity,
    ) -> None:
        """Remove shares from a holding."""
        holding = self._require_holding(instrument_id)
        holding.remove(quantity)

        if holding.available.value + holding.reserved.value == 0:
            self._holdings.pop(instrument_id)
            self._mark_holding_removed(instrument_id)
        else:
            self._mark_holding_updated(instrument_id)

    def reserve_holding(
        self,
        instrument_id: InstrumentId,
        quantity: Quantity,
    ) -> None:
        """Reserve shares."""
        self._require_holding(instrument_id).reserve(quantity)
        self._mark_holding_updated(instrument_id)

    def release_holding(
        self,
        instrument_id: InstrumentId,
        quantity: Quantity,
    ) -> None:
        """Release reserved shares."""
        self._require_holding(instrument_id).release(quantity)
        self._mark_holding_updated(instrument_id)

    def consume_reserved_holding(
        self,
        instrument_id: InstrumentId,
        quantity: Quantity,
    ) -> None:
        """Consume reserved shares after settlement."""
        self._require_holding(instrument_id).consume_reserved(quantity)
        self._mark_holding_updated(instrument_id)

    def lock(self) -> None:
        """Lock the wallet."""
        self.status = WalletStatus.LOCKED
        self._status_changed = True

    def activate(self) -> None:
        """Activate the wallet."""
        self.status = WalletStatus.ACTIVE
        self._status_changed = True

    def close(self) -> None:
        """Close the wallet."""
        self.status = WalletStatus.CLOSED
        self._status_changed = True

    def get_cash_changes(self) -> tuple[set[Currency], set[Currency]]:
        """Returns (created, updated) currencies."""
        return (
            self._created_cash.copy(),
            self._updated_cash.copy(),
        )

    def get_holding_changes(
        self,
    ) -> tuple[set[InstrumentId], set[InstrumentId], set[InstrumentId]]:
        """Returns (created, updated, removed) instrument IDs."""
        return (
            self._created_holdings.copy(),
            self._updated_holdings.copy(),
            self._removed_holdings.copy(),
        )

    def is_status_changed(self) -> bool:
        return self._status_changed

    def clear_changes(self) -> None:
        """Call after successful persistence."""
        self._status_changed = False
        self._created_cash.clear()
        self._updated_cash.clear()
        self._created_holdings.clear()
        self._updated_holdings.clear()
        self._removed_holdings.clear()

    def _get_cash_balance(self, currency: Currency) -> CashBalance | None:
        if currency in self._cash_balances:
            return self._cash_balances[currency]
        return None

    def _require_cash_balance(self, currency: Currency) -> CashBalance:
        balance = self._get_cash_balance(currency)

        if balance is None:
            raise CashBalanceNotFoundError(
                f"Cash balance for '{currency}' does not exist."
            )

        return balance

    def _get_holding(
        self,
        instrument_id: InstrumentId,
    ) -> Holding | None:
        if instrument_id in self._holdings:
            return self._holdings[instrument_id]
        return None

    def _require_holding(
        self,
        instrument_id: InstrumentId,
    ) -> Holding:
        holding = self._get_holding(instrument_id)

        if holding is None:
            raise HoldingNotFoundError("Holding does not exist.")

        return holding

    def _mark_cash_created(self, currency: Currency) -> None:
        self._created_cash.add(currency)
        self._updated_cash.discard(currency)

    def _mark_cash_updated(self, currency: Currency) -> None:
        if currency not in self._created_cash:
            self._updated_cash.add(currency)

    def _mark_holding_created(self, instrument_id: InstrumentId) -> None:
        self._created_holdings.add(instrument_id)
        self._updated_holdings.discard(instrument_id)
        self._removed_holdings.discard(instrument_id)

    def _mark_holding_updated(self, instrument_id: InstrumentId) -> None:
        if instrument_id not in self._created_holdings:
            self._updated_holdings.add(instrument_id)
        self._removed_holdings.discard(instrument_id)

    def _mark_holding_removed(self, instrument_id: InstrumentId) -> None:
        if instrument_id in self._created_holdings:
            self._created_holdings.discard(instrument_id)
        else:
            self._removed_holdings.add(instrument_id)
        self._updated_holdings.discard(instrument_id)
