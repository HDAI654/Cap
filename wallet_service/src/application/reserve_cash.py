from dataclasses import dataclass
from decimal import Decimal
from src.domain.ports.unit_of_work import UnitOfWork
from src.domain.value_objects.currency import Currency
from src.domain.value_objects.money import Money
from src.domain.value_objects.wallet_id import WalletId
from src.exceptions import InvalidCurrencyError


@dataclass(frozen=True, slots=True)
class ReserveCashCommand:
    """Input for the reserve-cash use case."""

    wallet_id: str
    amount: Decimal
    currency: str


class ReserveCashHandler:
    """Application service that reserves cash in a wallet."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def handle(self, command: ReserveCashCommand) -> None:
        """Reserve cash in the given wallet."""
        wallet_id = WalletId(command.wallet_id)
        try:
            currency = Currency(command.currency)
        except ValueError:
            raise InvalidCurrencyError("This currency is not supported")
        money = Money(command.amount, currency)

        async with self._uow:
            wallet = await self._uow.wallets.get_by_id(wallet_id)

            wallet.reserve_cash(money)
            await self._uow.wallets.update(wallet)
            await self._uow.commit()
