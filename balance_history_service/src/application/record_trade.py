import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from src.domain.entities.trade_record import TradeRecord
from src.domain.ports.unit_of_work import UnitOfWork
from src.exceptions import DuplicateTradeError

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class RecordTradeCommand:
    trade_id: str
    maker_order_id: str
    taker_order_id: str
    buyer_id: str
    seller_id: str
    instrument_id: str
    quantity: int
    execution_price: Decimal
    execution_price_currency: str
    sequence_number: int
    executed_at: datetime | None = None


class RecordTradeHandler:
    """Project a TradeExecuted event into the trade history store."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def handle(self, command: RecordTradeCommand) -> None:
        logger.info(
            "Recording trade: trade_id=%s instrument=%s qty=%s",
            command.trade_id,
            command.instrument_id,
            command.quantity,
        )
        async with self._uow:
            if await self._uow.trades.exists(command.trade_id):
                raise DuplicateTradeError(
                    f"Trade '{command.trade_id}' already recorded."
                )
            trade = TradeRecord(
                trade_id=command.trade_id,
                maker_order_id=command.maker_order_id,
                taker_order_id=command.taker_order_id,
                buyer_id=command.buyer_id,
                seller_id=command.seller_id,
                instrument_id=command.instrument_id,
                quantity=command.quantity,
                execution_price=command.execution_price,
                execution_price_currency=command.execution_price_currency,
                sequence_number=command.sequence_number,
                executed_at=command.executed_at
                or datetime.now(timezone.utc),
            )
            await self._uow.trades.add(trade)
            await self._uow.commit()
        logger.info("Trade recorded: trade_id=%s", command.trade_id)
