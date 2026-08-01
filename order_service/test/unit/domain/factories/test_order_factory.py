from src.domain.entities.order import Order
from src.domain.factories.order_factory import OrderFactory
from src.domain.value_objects.currency import Currency
from src.domain.value_objects.idempotency_key import IdempotencyKey
from src.domain.value_objects.instrument_id import InstrumentId
from src.domain.value_objects.money import Money
from src.domain.value_objects.order_side import OrderSide
from src.domain.value_objects.order_status import OrderStatus
from src.domain.value_objects.order_type import OrderType
from src.domain.value_objects.quantity import Quantity
from src.domain.value_objects.time_in_force import TimeInForce
from src.domain.value_objects.trader_id import TraderId


class TestOrderFactory:
    def test_create_limit_order(self):
        trader_id = TraderId.generate()
        instrument_id = InstrumentId.generate()
        key = IdempotencyKey("factory-limit-001")
        price = Money("12.34", Currency.USD)

        order = OrderFactory.create(
            trader_id=trader_id,
            instrument_id=instrument_id,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            time_in_force=TimeInForce.DAY,
            quantity=Quantity(25),
            idempotency_key=key,
            limit_price=price,
        )

        assert isinstance(order, Order)
        assert order.trader_id == trader_id
        assert order.instrument_id == instrument_id
        assert order.side is OrderSide.BUY
        assert order.order_type is OrderType.LIMIT
        assert order.time_in_force is TimeInForce.DAY
        assert order.quantity == Quantity(25)
        assert order.limit_price == price
        assert order.status is OrderStatus.NEW
        assert order.idempotency_key == key
        assert order.filled_quantity == Quantity(0)

    def test_create_market_order(self):
        order = OrderFactory.create(
            trader_id=TraderId.generate(),
            instrument_id=InstrumentId.generate(),
            side=OrderSide.SELL,
            order_type=OrderType.MARKET,
            time_in_force=TimeInForce.FOK,
            quantity=Quantity(10),
            idempotency_key=IdempotencyKey("factory-mkt-001"),
        )

        assert isinstance(order, Order)
        assert order.order_type is OrderType.MARKET
        assert order.limit_price is None
        assert order.status is OrderStatus.NEW
        assert order.side is OrderSide.SELL
        assert order.time_in_force is TimeInForce.FOK
