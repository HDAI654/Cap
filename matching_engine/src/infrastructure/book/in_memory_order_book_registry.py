from src.domain.entities.order_book import OrderBook
from src.domain.ports.order_book_registry import OrderBookRegistry
from src.domain.value_objects.instrument_id import InstrumentId


class InMemoryOrderBookRegistry(OrderBookRegistry):
    """Process-local registry of order books keyed by instrument."""

    def __init__(self) -> None:
        self._books: dict[str, OrderBook] = {}

    def get_or_create(self, instrument_id: InstrumentId) -> OrderBook:
        key = instrument_id.value
        book = self._books.get(key)
        if book is None:
            book = OrderBook(instrument_id)
            self._books[key] = book
        return book

    def get(self, instrument_id: InstrumentId) -> OrderBook | None:
        return self._books.get(instrument_id.value)
