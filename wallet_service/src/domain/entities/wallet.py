from shared.entity import Entity
from src.exceptions import InvalidValueError
from wallet_service.src.domain.entities.cash_balance import CashBalance
from wallet_service.src.domain.entities.holding import Holding
from wallet_service.src.domain.value_objects.wallet_status import WalletStatus
from wallet_service.src.domain.value_objects.currency import Currency
from wallet_service.src.domain.value_objects.instrument_id import InstrumentId
from wallet_service.src.domain.value_objects.money import Money
from wallet_service.src.domain.value_objects.quantity import Quantity
from wallet_service.src.domain.value_objects.trader_id import TraderId
from wallet_service.src.domain.value_objects.wallet_id import WalletId


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
        self.id = id
        self.trader_id = trader_id
        self.status = status

        self._cash_balances = cash_balances or []
        self._holdings = holdings or []

        super().__init__()

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
        return tuple(self._cash_balances)

    @property
    def holdings(self) -> tuple[Holding, ...]:
        """Return the wallet holdings."""
        return tuple(self._holdings)

    def deposit_cash(self, amount: Money) -> None:
        """Deposit cash into the wallet."""
        balance = self._get_cash_balance(amount.currency)

        if balance is None:
            balance = CashBalance(
                currency=amount.currency,
                available=Money(0, amount.currency),
                reserved=Money(0, amount.currency),
            )
            self._cash_balances.append(balance)

        balance.deposit(amount)

    def withdraw_cash(self, amount: Money) -> None:
        """Withdraw cash from the wallet."""
        self._require_cash_balance(amount.currency).withdraw(amount)

    def reserve_cash(self, amount: Money) -> None:
        """Reserve cash for an order."""
        self._require_cash_balance(amount.currency).reserve(amount)

    def release_cash(self, amount: Money) -> None:
        """Release reserved cash."""
        self._require_cash_balance(amount.currency).release(amount)

    def consume_reserved_cash(self, amount: Money) -> None:
        """Consume reserved cash after settlement."""
        self._require_cash_balance(amount.currency).consume_reserved(amount)

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
            self._holdings.append(holding)

        holding.add(quantity)
        holding.update_average_cost(average_cost)

    def remove_holding(
        self,
        instrument_id: InstrumentId,
        quantity: Quantity,
    ) -> None:
        """Remove shares from a holding."""
        self._require_holding(instrument_id).remove(quantity)

    def reserve_holding(
        self,
        instrument_id: InstrumentId,
        quantity: Quantity,
    ) -> None:
        """Reserve shares."""
        self._require_holding(instrument_id).reserve(quantity)

    def release_holding(
        self,
        instrument_id: InstrumentId,
        quantity: Quantity,
    ) -> None:
        """Release reserved shares."""
        self._require_holding(instrument_id).release(quantity)

    def consume_reserved_holding(
        self,
        instrument_id: InstrumentId,
        quantity: Quantity,
    ) -> None:
        """Consume reserved shares after settlement."""
        self._require_holding(instrument_id).consume_reserved(quantity)

    def lock(self) -> None:
        """Lock the wallet."""
        self.status = WalletStatus.LOCKED

    def activate(self) -> None:
        """Activate the wallet."""
        self.status = WalletStatus.ACTIVE

    def close(self) -> None:
        """Close the wallet."""
        self.status = WalletStatus.CLOSED

    def _get_cash_balance(self, currency: Currency) -> CashBalance | None:
        for balance in self._cash_balances:
            if balance.currency == currency:
                return balance
        return None

    def _require_cash_balance(self, currency: Currency) -> CashBalance:
        balance = self._get_cash_balance(currency)

        if balance is None:
            raise InvalidValueError(f"Cash balance for '{currency}' does not exist.")

        return balance

    def _get_holding(
        self,
        instrument_id: InstrumentId,
    ) -> Holding | None:
        for holding in self._holdings:
            if holding.instrument_id == instrument_id:
                return holding
        return None

    def _require_holding(
        self,
        instrument_id: InstrumentId,
    ) -> Holding:
        holding = self._get_holding(instrument_id)

        if holding is None:
            raise InvalidValueError("Holding does not exist.")

        return holding
