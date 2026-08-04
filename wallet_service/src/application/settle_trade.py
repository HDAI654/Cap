import logging
from dataclasses import dataclass
from decimal import Decimal

from src.domain.ports.unit_of_work import UnitOfWork
from src.domain.value_objects.currency import Currency
from src.domain.value_objects.instrument_id import InstrumentId
from src.domain.value_objects.money import Money
from src.domain.value_objects.quantity import Quantity
from src.domain.value_objects.trader_id import TraderId

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class SettleTradeCommand:
    """Settle a matched trade against buyer and seller wallets."""

    trade_id: str
    buyer_id: str
    seller_id: str
    instrument_id: str
    quantity: int
    execution_price: Decimal
    execution_price_currency: str


class SettleTradeHandler:
    """Consume reserved assets and credit the counterparties after a trade.

    Buyer: consume reserved cash (qty * price), add holdings.
    Seller: consume reserved holdings, deposit cash proceeds.
    """

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def handle(self, command: SettleTradeCommand) -> None:
        logger.info(
            "Settling trade: trade_id=%s buyer=%s seller=%s qty=%s price=%s",
            command.trade_id,
            command.buyer_id,
            command.seller_id,
            command.quantity,
            command.execution_price,
        )

        qty = Quantity(command.quantity)
        currency = Currency(command.execution_price_currency)
        notional = Money(
            command.execution_price * Decimal(command.quantity),
            currency,
        )
        instrument_id = InstrumentId(command.instrument_id)

        async with self._uow:
            buyer = await self._uow.wallets.get_by_trader_id(TraderId(command.buyer_id))
            seller = await self._uow.wallets.get_by_trader_id(
                TraderId(command.seller_id)
            )

            buyer.consume_reserved_cash(notional)
            buyer.add_holding(
                instrument_id=instrument_id,
                quantity=qty,
                average_cost=Money(command.execution_price, currency),
            )

            seller.consume_reserved_holding(instrument_id, qty)
            seller.deposit_cash(notional)

            await self._uow.wallets.update(buyer)
            await self._uow.wallets.update(seller)
            await self._uow.commit()

        logger.info("Trade settled: trade_id=%s", command.trade_id)
