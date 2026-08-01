from dataclasses import dataclass
from datetime import datetime, timezone

from shared.entity import Entity
from src.domain.value_objects.instrument_id import InstrumentId
from src.domain.value_objects.money import Money
from src.domain.value_objects.order_id import OrderId
from src.domain.value_objects.quantity import Quantity
from src.domain.value_objects.trade_id import TradeId
from src.domain.value_objects.trader_id import TraderId


class Trade(Entity):
    """Immutable record of a matched trade between maker and taker."""

    def __init__(
        self,
        id: TradeId,
        maker_order_id: OrderId,
        taker_order_id: OrderId,
        buyer_id: TraderId,
        seller_id: TraderId,
        instrument_id: InstrumentId,
        quantity: Quantity,
        execution_price: Money,
        sequence_number: int,
        executed_at: datetime,
    ) -> None:
        self.id = id
        self.maker_order_id = maker_order_id
        self.taker_order_id = taker_order_id
        self.buyer_id = buyer_id
        self.seller_id = seller_id
        self.instrument_id = instrument_id
        self.quantity = quantity
        self.execution_price = execution_price
        self.sequence_number = sequence_number
        self.executed_at = executed_at

    @classmethod
    def create(
        cls,
        maker_order_id: OrderId,
        taker_order_id: OrderId,
        buyer_id: TraderId,
        seller_id: TraderId,
        instrument_id: InstrumentId,
        quantity: Quantity,
        execution_price: Money,
        sequence_number: int,
    ) -> "Trade":
        return cls(
            id=TradeId.generate(),
            maker_order_id=maker_order_id,
            taker_order_id=taker_order_id,
            buyer_id=buyer_id,
            seller_id=seller_id,
            instrument_id=instrument_id,
            quantity=quantity,
            execution_price=execution_price,
            sequence_number=sequence_number,
            executed_at=datetime.now(timezone.utc),
        )
