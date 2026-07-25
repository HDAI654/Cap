from dataclasses import dataclass
from src.domain.ports.unit_of_work import UnitOfWork
from src.domain.value_objects.wallet_id import WalletId
from src.application.DTOs import CashBalanceDTO, HoldingDTO, WalletDTO


@dataclass(frozen=True, slots=True)
class GetWalletQuery:
    """Input for the get-wallet use case."""

    wallet_id: str


class GetWalletHandler:
    """Application service that retrieves a wallet by identifier."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def handle(self, query: GetWalletQuery) -> WalletDTO:
        """Retrieve a wallet."""
        wallet_id = WalletId(query.wallet_id)

        async with self._uow:
            wallet = await self._uow.wallets.get_by_id(wallet_id)

            return WalletDTO(
                wallet_id=wallet.id.value,
                trader_id=wallet.trader_id.value,
                status=wallet.status.value,
                cash_balances=tuple(
                    CashBalanceDTO(
                        currency=balance.currency.value,
                        available=balance.available.amount,
                        reserved=balance.reserved.amount,
                    )
                    for balance in wallet.cash_balances
                ),
                holdings=tuple(
                    HoldingDTO(
                        instrument_id=holding.instrument_id.value,
                        available=holding.available.value,
                        reserved=holding.reserved.value,
                        average_cost=holding.average_cost.amount,
                        average_cost_currency=holding.average_cost.currency.value,
                    )
                    for holding in wallet.holdings
                ),
            )
