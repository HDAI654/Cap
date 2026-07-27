from dataclasses import dataclass
from src.domain.factories.wallet_factory import WalletFactory
from src.domain.ports.unit_of_work import UnitOfWork
from src.domain.value_objects.trader_id import TraderId
from src.exceptions import WalletAlreadyExistsError


@dataclass(frozen=True, slots=True)
class CreateWalletCommand:
    """Input for the create-wallet use case."""

    trader_id: str


@dataclass(frozen=True, slots=True)
class CreateWalletResult:
    """Output of the create-wallet use case."""

    wallet_id: str


class CreateWalletHandler:
    """Application service that creates a wallet for a trader."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def handle(self, command: CreateWalletCommand) -> CreateWalletResult:
        """Create a new wallet.

        Raises:
            WalletAlreadyExistsError: If a wallet already exists for the trader.
        """
        trader_id = TraderId(command.trader_id)

        async with self._uow:
            if await self._uow.wallets.exists_by_trader_id(trader_id):
                raise WalletAlreadyExistsError(
                    f"Wallet already exists for trader '{command.trader_id}'."
                )

            wallet = WalletFactory.create(trader_id=trader_id)
            await self._uow.wallets.add(wallet)
            await self._uow.commit()
            wallet.clear_changes()

            return CreateWalletResult(wallet_id=wallet.id.value)
