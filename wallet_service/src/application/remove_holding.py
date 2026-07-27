from dataclasses import dataclass
from src.domain.ports.unit_of_work import UnitOfWork
from src.domain.value_objects.instrument_id import InstrumentId
from src.domain.value_objects.quantity import Quantity
from src.domain.value_objects.wallet_id import WalletId


@dataclass(frozen=True, slots=True)
class RemoveHoldingCommand:
    """Input for the remove-holding use case."""

    wallet_id: str
    instrument_id: str
    quantity: int


class RemoveHoldingHandler:
    """Application service that removes shares from a wallet holding."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def handle(self, command: RemoveHoldingCommand) -> None:
        """Remove shares from a holding in the given wallet."""
        wallet_id = WalletId(command.wallet_id)
        instrument_id = InstrumentId(command.instrument_id)
        quantity = Quantity(command.quantity)

        async with self._uow:
            wallet = await self._uow.wallets.get_by_id(wallet_id)

            wallet.remove_holding(instrument_id, quantity)
            await self._uow.wallets.update(wallet)
            await self._uow.commit()
