from decimal import Decimal

from src.domain.read_models.order_book_snapshot import (
    LastTradePrice,
    OrderBookSnapshot,
    PriceLevel,
)
from src.domain.value_objects.instrument_id import InstrumentId
from src.infrastructure.cache.in_memory_market_data_reader import (
    InMemoryMarketDataReader,
)


async def test_seed_and_get_book() -> None:
    reader = InMemoryMarketDataReader()
    instrument_id = InstrumentId.generate()
    snapshot = OrderBookSnapshot(
        instrument_id=instrument_id.value,
        bids=(PriceLevel(price=Decimal("1.00"), quantity=10),),
        asks=(PriceLevel(price=Decimal("1.10"), quantity=5),),
        last_trade_price=None,
        last_trade_currency=None,
    )
    reader.seed_book(snapshot)

    loaded = await reader.get_order_book(instrument_id)

    assert loaded is not None
    assert loaded.bids[0].quantity == 10
    assert await reader.get_order_book(InstrumentId.generate()) is None


async def test_seed_and_get_ltp() -> None:
    reader = InMemoryMarketDataReader()
    instrument_id = InstrumentId.generate()
    ltp = LastTradePrice(
        instrument_id=instrument_id.value,
        price=Decimal("42.50"),
        currency="USD",
    )
    reader.seed_ltp(ltp)

    loaded = await reader.get_last_trade_price(instrument_id)

    assert loaded is not None
    assert loaded.price == Decimal("42.50")
    assert await reader.get_last_trade_price(InstrumentId.generate()) is None
