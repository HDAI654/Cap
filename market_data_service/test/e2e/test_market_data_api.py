import uuid

from fastapi.testclient import TestClient

from src.domain.value_objects.instrument_id import InstrumentId

BASE = "/api/v1/market-data"


class TestOrderBook:
    def test_get_order_book(self, client: TestClient, instrument_id: str) -> None:
        response = client.get(f"{BASE}/{instrument_id}/order-book")
        assert response.status_code == 200
        body = response.json()
        assert body["instrument_id"] == instrument_id
        assert len(body["bids"]) == 2
        assert body["bids"][0]["price"] == "100.00"
        assert body["bids"][0]["quantity"] == 50
        assert len(body["asks"]) == 1
        assert body["last_trade_price"] == "100.25"
        assert body["last_trade_currency"] == "USD"

    def test_order_book_not_found(self, client: TestClient) -> None:
        missing = InstrumentId.generate().value
        response = client.get(f"{BASE}/{missing}/order-book")
        assert response.status_code == 404

    def test_invalid_instrument_id(self, client: TestClient) -> None:
        response = client.get(f"{BASE}/not-a-uuid/order-book")
        assert response.status_code == 422


class TestLastTradePrice:
    def test_get_ltp(self, client: TestClient, instrument_id: str) -> None:
        response = client.get(f"{BASE}/{instrument_id}/last-trade-price")
        assert response.status_code == 200
        body = response.json()
        assert body["instrument_id"] == instrument_id
        assert body["price"] == "100.25"
        assert body["currency"] == "USD"

    def test_ltp_not_found(self, client: TestClient) -> None:
        missing = str(uuid.uuid4())
        response = client.get(f"{BASE}/{missing}/last-trade-price")
        assert response.status_code == 404
