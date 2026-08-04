import logging
from dataclasses import dataclass

from src.application.DTOs import CashBalanceDTO, HoldingDTO, WalletDTO
from src.domain.ports.unit_of_work import UnitOfWork
from src.domain.value_objects.trader_id import TraderId

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class GetWalletByTraderQuery:
    trader_id: str


class GetWalletByTraderHandler:
    """Retrieve a wallet by owning trader id."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def handle(self, query: GetWalletByTraderQuery) -> WalletDTO:
        logger.info("Retrieving wallet by trader: trader_id=%s", query.trader_id)
        trader_id = TraderId(query.trader_id)

        async with self._uow:
            wallet = await self._uow.wallets.get_by_trader_id(trader_id)

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
