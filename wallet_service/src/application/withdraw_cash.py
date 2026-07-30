import logging
from dataclasses import dataclass
from decimal import Decimal
from src.domain.ports.unit_of_work import UnitOfWork
from src.domain.value_objects.currency import Currency
from src.domain.value_objects.money import Money
from src.domain.value_objects.wallet_id import WalletId
from src.exceptions import InvalidCurrencyError

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class WithdrawCashCommand:
    """Input for the withdraw-cash use case."""

    wallet_id: str
    amount: Decimal
    currency: str


class WithdrawCashHandler:
    """Application service that withdraws cash from a wallet."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def handle(self, command: WithdrawCashCommand) -> None:
        """Withdraw cash from the given wallet."""
        logger.info(
            "Withdrawing cash: wallet_id=%s, amount=%s, currency=%s",
            command.wallet_id,
            command.amount,
            command.currency,
        )

        wallet_id = WalletId(command.wallet_id)
        try:
            currency = Currency(command.currency)
        except ValueError:
            raise InvalidCurrencyError("This currency is not supported")
        money = Money(command.amount, currency)

        async with self._uow:
            wallet = await self._uow.wallets.get_by_id(wallet_id)

            wallet.withdraw_cash(money)
            await self._uow.wallets.update(wallet)
            await self._uow.commit()
            wallet.clear_changes()

        logger.info(
            "Cash withdrawn successfully: wallet_id=%s, amount=%s, currency=%s",
            command.wallet_id,
            command.amount,
            command.currency,
        )
