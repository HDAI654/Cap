from dataclasses import dataclass
from src.domain.ports.unit_of_work import UnitOfWork
from src.domain.value_objects.wallet_id import WalletId


@dataclass(frozen=True, slots=True)
class CloseWalletCommand:
    """Input for the close-wallet use case."""

    wallet_id: str


class CloseWalletHandler:
    """Application service that closes a wallet."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def handle(self, command: CloseWalletCommand) -> None:
        """Close the given wallet."""
        wallet_id = WalletId(command.wallet_id)

        async with self._uow:
            wallet = await self._uow.wallets.get_by_id(wallet_id)

            wallet.close()

            if wallet.is_changed():
                await self._uow.wallets.update(wallet)
                await self._uow.commit()
                wallet.clear_changes()
