import logging
from dataclasses import dataclass
from decimal import Decimal
from src.domain.ports.unit_of_work import UnitOfWork
from src.domain.value_objects.currency import Currency
from src.domain.value_objects.instrument_id import InstrumentId
from src.domain.value_objects.money import Money
from src.domain.value_objects.quantity import Quantity
from src.domain.value_objects.wallet_id import WalletId
from src.exceptions import InvalidCurrencyError

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class AddHoldingCommand:
    """Input for the add-holding use case."""

    wallet_id: str
    instrument_id: str
    quantity: int
    average_cost: Decimal
    average_cost_currency: str


class AddHoldingHandler:
    """Application service that adds shares to a wallet holding."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def handle(self, command: AddHoldingCommand) -> None:
        """Add shares to a holding in the given wallet."""
        logger.info(
            "Adding shares to a holding in the given wallet: wallet_id=%s, instrument_id=%s, quantity=%s",
            command.wallet_id,
            command.instrument_id,
            command.quantity,
        )

        wallet_id = WalletId(command.wallet_id)
        instrument_id = InstrumentId(command.instrument_id)
        quantity = Quantity(command.quantity)
        try:
            average_cost_currency = Currency(command.average_cost_currency)
        except ValueError:
            raise InvalidCurrencyError("This currency is not supported")
        average_cost = Money(
            command.average_cost,
            average_cost_currency,
        )

        async with self._uow:
            wallet = await self._uow.wallets.get_by_id(wallet_id)

            wallet.add_holding(instrument_id, quantity, average_cost)
            await self._uow.wallets.update(wallet)
            await self._uow.commit()
            wallet.clear_changes()

        logger.info(
            "Shares are added successfully: wallet_id=%s, instrument_id=%s, quantity=%s",
            command.wallet_id,
            command.instrument_id,
            command.quantity,
        )
