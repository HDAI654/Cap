import uuid
from copy import deepcopy

from fastapi.testclient import TestClient

BASE = "/api/v1/orders"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_order(client: TestClient, order_id: str) -> dict:
    response = client.get(f"{BASE}/{order_id}")
    assert response.status_code == 200, response.text
    return response.json()


def _submit(client: TestClient, payload: dict) -> str:
    response = client.post(BASE, json=payload)
    assert response.status_code == 201, response.text
    return response.json()["order_id"]


# ---------------------------------------------------------------------------
# Submit
# ---------------------------------------------------------------------------


class TestSubmitOrder:
    """POST /api/v1/orders"""

    def test_submits_limit_order_returns_201(
        self,
        client: TestClient,
        limit_order_payload: dict,
    ) -> None:
        response = client.post(BASE, json=limit_order_payload)

        assert response.status_code == 201
        body = response.json()
        assert "order_id" in body
        uuid.UUID(body["order_id"], version=4)

    def test_submits_market_order_returns_201(
        self,
        client: TestClient,
        market_order_payload: dict,
    ) -> None:
        response = client.post(BASE, json=market_order_payload)

        assert response.status_code == 201
        assert "order_id" in response.json()

    def test_duplicate_idempotency_key_returns_409(
        self,
        client: TestClient,
        limit_order_payload: dict,
    ) -> None:
        first = client.post(BASE, json=limit_order_payload)
        assert first.status_code == 201

        second = client.post(BASE, json=limit_order_payload)

        assert second.status_code == 409
        assert "detail" in second.json()

    def test_invalid_side_returns_422(
        self,
        client: TestClient,
        limit_order_payload: dict,
    ) -> None:
        payload = deepcopy(limit_order_payload)
        payload["side"] = "HOLD"
        response = client.post(BASE, json=payload)

        assert response.status_code == 422

    def test_invalid_order_type_returns_422(
        self,
        client: TestClient,
        limit_order_payload: dict,
    ) -> None:
        payload = deepcopy(limit_order_payload)
        payload["order_type"] = "STOP"
        response = client.post(BASE, json=payload)

        assert response.status_code == 422

    def test_invalid_time_in_force_returns_422(
        self,
        client: TestClient,
        limit_order_payload: dict,
    ) -> None:
        payload = deepcopy(limit_order_payload)
        payload["time_in_force"] = "GTD"
        response = client.post(BASE, json=payload)

        assert response.status_code == 422

    def test_limit_without_price_returns_422(
        self,
        client: TestClient,
        limit_order_payload: dict,
    ) -> None:
        payload = deepcopy(limit_order_payload)
        payload.pop("limit_price")
        payload.pop("limit_price_currency")
        response = client.post(BASE, json=payload)

        assert response.status_code == 422

    def test_market_with_price_returns_422(
        self,
        client: TestClient,
        market_order_payload: dict,
    ) -> None:
        payload = deepcopy(market_order_payload)
        payload["limit_price"] = "1.00"
        payload["limit_price_currency"] = "USD"
        response = client.post(BASE, json=payload)

        assert response.status_code == 422

    def test_zero_quantity_returns_422(
        self,
        client: TestClient,
        limit_order_payload: dict,
    ) -> None:
        payload = deepcopy(limit_order_payload)
        payload["quantity"] = 0
        response = client.post(BASE, json=payload)

        assert response.status_code == 422

    def test_invalid_trader_id_returns_422(
        self,
        client: TestClient,
        limit_order_payload: dict,
    ) -> None:
        payload = deepcopy(limit_order_payload)
        payload["trader_id"] = "not-a-uuid"
        response = client.post(BASE, json=payload)

        assert response.status_code == 422


# ---------------------------------------------------------------------------
# Get / list
# ---------------------------------------------------------------------------


class TestGetOrder:
    """GET /api/v1/orders/{order_id}"""

    def test_returns_full_projection(
        self,
        client: TestClient,
        submitted_limit_order: dict,
    ) -> None:
        order_id = submitted_limit_order["order_id"]
        body = _get_order(client, order_id)

        assert body["order_id"] == order_id
        assert body["trader_id"] == submitted_limit_order["trader_id"]
        assert body["instrument_id"] == submitted_limit_order["instrument_id"]
        assert body["side"] == "BUY"
        assert body["order_type"] == "LIMIT"
        assert body["time_in_force"] == "GTC"
        assert body["quantity"] == 100
        assert body["filled_quantity"] == 0
        assert body["remaining_quantity"] == 100
        assert str(body["limit_price"]) in ("10.50", "10.5")
        assert body["limit_price_currency"] == "USD"
        assert body["status"] == "OPEN"
        assert body["idempotency_key"] == submitted_limit_order["idempotency_key"]
        assert "created_at" in body
        assert "updated_at" in body

    def test_market_order_has_null_price(
        self,
        client: TestClient,
        market_order_payload: dict,
    ) -> None:
        order_id = _submit(client, market_order_payload)
        body = _get_order(client, order_id)

        assert body["order_type"] == "MARKET"
        assert body["limit_price"] is None
        assert body["limit_price_currency"] is None

    def test_unknown_order_returns_404(self, client: TestClient) -> None:
        missing_id = str(uuid.uuid4())
        response = client.get(f"{BASE}/{missing_id}")

        assert response.status_code == 404
        assert "detail" in response.json()

    def test_invalid_order_id_path_returns_422(self, client: TestClient) -> None:
        response = client.get(f"{BASE}/not-a-uuid")

        assert response.status_code == 422


class TestListOrdersByTrader:
    """GET /api/v1/orders?trader_id="""

    def test_returns_orders_for_trader(
        self,
        client: TestClient,
        limit_order_payload: dict,
        market_order_payload: dict,
    ) -> None:
        _submit(client, limit_order_payload)
        _submit(client, market_order_payload)

        response = client.get(
            BASE,
            params={"trader_id": limit_order_payload["trader_id"]},
        )

        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_empty_for_unknown_trader(self, client: TestClient) -> None:
        response = client.get(
            BASE,
            params={"trader_id": str(uuid.uuid4())},
        )

        assert response.status_code == 200
        assert response.json() == []

    def test_invalid_trader_id_returns_422(self, client: TestClient) -> None:
        response = client.get(BASE, params={"trader_id": "not-a-uuid"})

        assert response.status_code == 422


# ---------------------------------------------------------------------------
# Lifecycle transitions
# ---------------------------------------------------------------------------


class TestOpenOrder:
    """POST /api/v1/orders/{order_id}/open"""

    def test_submit_already_opens_order(
        self,
        client: TestClient,
        submitted_limit_order: dict,
    ) -> None:
        """Submit path opens the order; explicit open is idempotent-conflict."""
        order_id = submitted_limit_order["order_id"]
        assert _get_order(client, order_id)["status"] == "OPEN"

    def test_already_open_returns_409(
        self,
        client: TestClient,
        submitted_limit_order: dict,
    ) -> None:
        order_id = submitted_limit_order["order_id"]
        client.post(f"{BASE}/{order_id}/open")

        response = client.post(f"{BASE}/{order_id}/open")

        assert response.status_code == 409

    def test_missing_order_returns_404(self, client: TestClient) -> None:
        response = client.post(f"{BASE}/{uuid.uuid4()}/open")

        assert response.status_code == 404


class TestFillOrder:
    """POST /api/v1/orders/{order_id}/fills"""

    def test_partial_fill(
        self,
        client: TestClient,
        submitted_limit_order: dict,
    ) -> None:
        order_id = submitted_limit_order["order_id"]
        client.post(f"{BASE}/{order_id}/open")

        response = client.post(
            f"{BASE}/{order_id}/fills",
            json={"fill_quantity": 40},
        )

        assert response.status_code == 204
        body = _get_order(client, order_id)
        assert body["status"] == "PARTIALLY_FILLED"
        assert body["filled_quantity"] == 40
        assert body["remaining_quantity"] == 60

    def test_full_fill(
        self,
        client: TestClient,
        submitted_limit_order: dict,
    ) -> None:
        order_id = submitted_limit_order["order_id"]
        client.post(f"{BASE}/{order_id}/open")

        response = client.post(
            f"{BASE}/{order_id}/fills",
            json={"fill_quantity": 100},
        )

        assert response.status_code == 204
        body = _get_order(client, order_id)
        assert body["status"] == "FILLED"
        assert body["filled_quantity"] == 100
        assert body["remaining_quantity"] == 0

    def test_overfill_returns_422(
        self,
        client: TestClient,
        submitted_limit_order: dict,
    ) -> None:
        order_id = submitted_limit_order["order_id"]
        client.post(f"{BASE}/{order_id}/open")

        response = client.post(
            f"{BASE}/{order_id}/fills",
            json={"fill_quantity": 101},
        )

        assert response.status_code == 422

    def test_fill_auto_opened_order_succeeds(
        self,
        client: TestClient,
        submitted_limit_order: dict,
    ) -> None:
        order_id = submitted_limit_order["order_id"]
        response = client.post(
            f"{BASE}/{order_id}/fills",
            json={"fill_quantity": 10},
        )
        assert response.status_code == 204

    def test_missing_order_returns_404(self, client: TestClient) -> None:
        response = client.post(
            f"{BASE}/{uuid.uuid4()}/fills",
            json={"fill_quantity": 1},
        )

        assert response.status_code == 404


class TestCancelOrder:
    """POST /api/v1/orders/{order_id}/cancel"""

    def test_cancels_open_order(
        self,
        client: TestClient,
        submitted_limit_order: dict,
    ) -> None:
        order_id = submitted_limit_order["order_id"]
        client.post(f"{BASE}/{order_id}/open")

        response = client.post(f"{BASE}/{order_id}/cancel")

        assert response.status_code == 204
        assert _get_order(client, order_id)["status"] == "CANCELLED"

    def test_cancels_partially_filled_preserves_fill(
        self,
        client: TestClient,
        submitted_limit_order: dict,
    ) -> None:
        order_id = submitted_limit_order["order_id"]
        client.post(f"{BASE}/{order_id}/open")
        client.post(f"{BASE}/{order_id}/fills", json={"fill_quantity": 25})

        response = client.post(f"{BASE}/{order_id}/cancel")

        assert response.status_code == 204
        body = _get_order(client, order_id)
        assert body["status"] == "CANCELLED"
        assert body["filled_quantity"] == 25

    def test_cancel_filled_returns_409(
        self,
        client: TestClient,
        submitted_limit_order: dict,
    ) -> None:
        order_id = submitted_limit_order["order_id"]
        client.post(f"{BASE}/{order_id}/open")
        client.post(f"{BASE}/{order_id}/fills", json={"fill_quantity": 100})

        response = client.post(f"{BASE}/{order_id}/cancel")

        assert response.status_code == 409

    def test_missing_order_returns_404(self, client: TestClient) -> None:
        response = client.post(f"{BASE}/{uuid.uuid4()}/cancel")

        assert response.status_code == 404


class TestRejectOrder:
    """POST /api/v1/orders/{order_id}/reject"""

    def test_reject_after_auto_open_returns_409(
        self,
        client: TestClient,
        submitted_limit_order: dict,
    ) -> None:
        """Submit auto-opens; only NEW orders can be rejected."""
        order_id = submitted_limit_order["order_id"]
        response = client.post(f"{BASE}/{order_id}/reject")
        assert response.status_code == 409

    def test_reject_open_returns_409(
        self,
        client: TestClient,
        submitted_limit_order: dict,
    ) -> None:
        order_id = submitted_limit_order["order_id"]
        client.post(f"{BASE}/{order_id}/open")

        response = client.post(f"{BASE}/{order_id}/reject")

        assert response.status_code == 409


class TestExpireOrder:
    """POST /api/v1/orders/{order_id}/expire"""

    def test_expires_open_order(
        self,
        client: TestClient,
        submitted_limit_order: dict,
    ) -> None:
        order_id = submitted_limit_order["order_id"]
        client.post(f"{BASE}/{order_id}/open")

        response = client.post(f"{BASE}/{order_id}/expire")

        assert response.status_code == 204
        assert _get_order(client, order_id)["status"] == "EXPIRED"

    def test_expire_auto_opened_order_succeeds(
        self,
        client: TestClient,
        submitted_limit_order: dict,
    ) -> None:
        order_id = submitted_limit_order["order_id"]
        response = client.post(f"{BASE}/{order_id}/expire")
        assert response.status_code == 204
        assert _get_order(client, order_id)["status"] == "EXPIRED"


# ---------------------------------------------------------------------------
# Full journeys
# ---------------------------------------------------------------------------


class TestOrderJourneys:
    """End-to-end lifecycle scenarios."""

    def test_full_fill_journey(
        self,
        client: TestClient,
        limit_order_payload: dict,
    ) -> None:
        """Submit (auto-open) → partial fill → complete fill."""
        order_id = _submit(client, limit_order_payload)
        assert _get_order(client, order_id)["status"] == "OPEN"

        assert (
            client.post(
                f"{BASE}/{order_id}/fills",
                json={"fill_quantity": 30},
            ).status_code
            == 204
        )
        body = _get_order(client, order_id)
        assert body["status"] == "PARTIALLY_FILLED"
        assert body["filled_quantity"] == 30
        assert body["remaining_quantity"] == 70

        assert (
            client.post(
                f"{BASE}/{order_id}/fills",
                json={"fill_quantity": 70},
            ).status_code
            == 204
        )
        body = _get_order(client, order_id)
        assert body["status"] == "FILLED"
        assert body["filled_quantity"] == 100
        assert body["remaining_quantity"] == 0

    def test_cancel_after_partial_fill_journey(
        self,
        client: TestClient,
        limit_order_payload: dict,
    ) -> None:
        """Submit (auto-open) → partial fill → cancel."""
        order_id = _submit(client, limit_order_payload)
        client.post(f"{BASE}/{order_id}/fills", json={"fill_quantity": 40})
        client.post(f"{BASE}/{order_id}/cancel")

        body = _get_order(client, order_id)
        assert body["status"] == "CANCELLED"
        assert body["filled_quantity"] == 40
        assert body["remaining_quantity"] == 60

    def test_reject_auto_opened_order_journey(
        self,
        client: TestClient,
        market_order_payload: dict,
    ) -> None:
        """Submit MARKET auto-opens; reject is no longer valid."""
        order_id = _submit(client, market_order_payload)
        assert _get_order(client, order_id)["status"] == "OPEN"
        assert client.post(f"{BASE}/{order_id}/reject").status_code == 409
