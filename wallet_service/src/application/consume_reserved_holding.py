from dataclasses import dataclass
from src.domain.ports.unit_of_work import UnitOfWork
from src.domain.value_objects.instrument_id import InstrumentId
from src.domain.value_objects.quantity import Quantity
from src.domain.value_objects.wallet_id import WalletId
from src.exceptions import WalletNotFoundError


@dataclass(frozen=True, slots=True)
class ConsumeReservedHoldingCommand:
    """Input for the consume-reserved-holding use case."""

    wallet_id: str
    instrument_id: str
    quantity: int


class ConsumeReservedHoldingHandler:
    """Application service that consumes reserved shares after settlement."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def handle(self, command: ConsumeReservedHoldingCommand) -> None:
        """Consume reserved shares in a holding of the given wallet."""
        wallet_id = WalletId(command.wallet_id)
        instrument_id = InstrumentId(command.instrument_id)
        quantity = Quantity(command.quantity)

        async with self._uow:
            wallet = await self._uow.wallets.get_by_id(wallet_id)

            wallet.consume_reserved_holding(instrument_id, quantity)
            await self._uow.wallets.update(wallet)
            await self._uow.commit()
            wallet.clear_changes()
