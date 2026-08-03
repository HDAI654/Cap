import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from src.domain.entities.order_history_entry import OrderHistoryEntry
from src.domain.ports.unit_of_work import UnitOfWork

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class RecordOrderEventCommand:
    order_id: str
    trader_id: str
    instrument_id: str
    event_type: str
    side: str | None = None
    order_type: str | None = None
    quantity: int | None = None
    filled_quantity: int | None = None
    remaining_quantity: int | None = None
    price: Decimal | None = None
    price_currency: str | None = None
    status: str | None = None
    occurred_at: datetime | None = None


class RecordOrderEventHandler:
    """Append an order lifecycle event to order history."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def handle(self, command: RecordOrderEventCommand) -> None:
        logger.info(
            "Recording order event: order_id=%s event_type=%s",
            command.order_id,
            command.event_type,
        )
        entry = OrderHistoryEntry(
            entry_id=str(uuid.uuid4()),
            order_id=command.order_id,
            trader_id=command.trader_id,
            instrument_id=command.instrument_id,
            event_type=command.event_type,
            side=command.side,
            order_type=command.order_type,
            quantity=command.quantity,
            filled_quantity=command.filled_quantity,
            remaining_quantity=command.remaining_quantity,
            price=command.price,
            price_currency=command.price_currency,
            status=command.status,
            occurred_at=command.occurred_at or datetime.now(timezone.utc),
        )
        async with self._uow:
            await self._uow.order_history.add(entry)
            await self._uow.commit()
        logger.info(
            "Order event recorded: order_id=%s event_type=%s",
            command.order_id,
            command.event_type,
        )
