from src.domain.entities.order_history_entry import OrderHistoryEntry
from src.domain.entities.trade_record import TradeRecord
from src.infrastructure.persistence.models import OrderHistoryModel, TradeModel


def trade_to_model(trade: TradeRecord) -> TradeModel:
    return TradeModel(
        trade_id=trade.trade_id,
        maker_order_id=trade.maker_order_id,
        taker_order_id=trade.taker_order_id,
        buyer_id=trade.buyer_id,
        seller_id=trade.seller_id,
        instrument_id=trade.instrument_id,
        quantity=trade.quantity,
        execution_price=trade.execution_price,
        execution_price_currency=trade.execution_price_currency,
        sequence_number=trade.sequence_number,
        executed_at=trade.executed_at,
    )


def model_to_trade(model: TradeModel) -> TradeRecord:
    return TradeRecord(
        trade_id=model.trade_id,
        maker_order_id=model.maker_order_id,
        taker_order_id=model.taker_order_id,
        buyer_id=model.buyer_id,
        seller_id=model.seller_id,
        instrument_id=model.instrument_id,
        quantity=model.quantity,
        execution_price=model.execution_price,
        execution_price_currency=model.execution_price_currency,
        sequence_number=model.sequence_number,
        executed_at=model.executed_at,
    )


def entry_to_model(entry: OrderHistoryEntry) -> OrderHistoryModel:
    return OrderHistoryModel(
        entry_id=entry.entry_id,
        order_id=entry.order_id,
        trader_id=entry.trader_id,
        instrument_id=entry.instrument_id,
        event_type=entry.event_type,
        side=entry.side,
        order_type=entry.order_type,
        quantity=entry.quantity,
        filled_quantity=entry.filled_quantity,
        remaining_quantity=entry.remaining_quantity,
        price=entry.price,
        price_currency=entry.price_currency,
        status=entry.status,
        occurred_at=entry.occurred_at,
    )


def model_to_entry(model: OrderHistoryModel) -> OrderHistoryEntry:
    return OrderHistoryEntry(
        entry_id=model.entry_id,
        order_id=model.order_id,
        trader_id=model.trader_id,
        instrument_id=model.instrument_id,
        event_type=model.event_type,
        side=model.side,
        order_type=model.order_type,
        quantity=model.quantity,
        filled_quantity=model.filled_quantity,
        remaining_quantity=model.remaining_quantity,
        price=model.price,
        price_currency=model.price_currency,
        status=model.status,
        occurred_at=model.occurred_at,
    )
