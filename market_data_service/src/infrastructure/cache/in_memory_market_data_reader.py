from src.domain.ports.market_data_reader import MarketDataReader
from src.domain.read_models.order_book_snapshot import LastTradePrice, OrderBookSnapshot
from src.domain.value_objects.instrument_id import InstrumentId


class InMemoryMarketDataReader(MarketDataReader):
    """Process-local store for tests and Redis-disabled runs."""

    def __init__(self) -> None:
        self._books: dict[str, OrderBookSnapshot] = {}
        self._ltp: dict[str, LastTradePrice] = {}

    def seed_book(self, snapshot: OrderBookSnapshot) -> None:
        self._books[snapshot.instrument_id] = snapshot

    def seed_ltp(self, ltp: LastTradePrice) -> None:
        self._ltp[ltp.instrument_id] = ltp

    async def get_order_book(
        self,
        instrument_id: InstrumentId,
    ) -> OrderBookSnapshot | None:
        return self._books.get(instrument_id.value)

    async def get_last_trade_price(
        self,
        instrument_id: InstrumentId,
    ) -> LastTradePrice | None:
        return self._ltp.get(instrument_id.value)
