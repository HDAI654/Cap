import uuid
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

BASE = "/api/v1/wallets"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_wallet(client: TestClient, wallet_id: str) -> dict:
    response = client.get(f"{BASE}/{wallet_id}")
    assert response.status_code == 200, response.text
    return response.json()


def _cash(wallet: dict, currency: str = "USD") -> dict | None:
    for balance in wallet["cash_balances"]:
        if balance["currency"] == currency:
            return balance
    return None


def _holding(wallet: dict, instrument_id: str) -> dict | None:
    for holding in wallet["holdings"]:
        if holding["instrument_id"] == instrument_id:
            return holding
    return None


# ---------------------------------------------------------------------------
# Wallet lifecycle
# ---------------------------------------------------------------------------


class TestCreateWallet:
    """POST /api/v1/wallets"""

    def test_creates_wallet_and_returns_201(
        self,
        client: TestClient,
        trader_id: str,
    ) -> None:
        response = client.post(BASE, json={"trader_id": trader_id})

        assert response.status_code == 201
        body = response.json()
        assert "wallet_id" in body
        uuid.UUID(body["wallet_id"], version=4)

    def test_created_wallet_is_active_and_empty(
        self,
        client: TestClient,
        created_wallet: dict[str, str],
    ) -> None:
        wallet = _get_wallet(client, created_wallet["wallet_id"])

        assert wallet["wallet_id"] == created_wallet["wallet_id"]
        assert wallet["trader_id"] == created_wallet["trader_id"]
        assert wallet["status"] == "ACTIVE"
        assert wallet["cash_balances"] == []
        assert wallet["holdings"] == []

    def test_duplicate_trader_returns_409(
        self,
        client: TestClient,
        created_wallet: dict[str, str],
    ) -> None:
        response = client.post(
            BASE,
            json={"trader_id": created_wallet["trader_id"]},
        )

        assert response.status_code == 409
        assert "detail" in response.json()

    def test_invalid_trader_id_returns_422(
        self,
        client: TestClient,
    ) -> None:
        response = client.post(BASE, json={"trader_id": "not-a-uuid"})

        assert response.status_code == 422


class TestGetWallet:
    """GET /api/v1/wallets/{wallet_id}"""

    def test_unknown_wallet_returns_404(self, client: TestClient) -> None:
        missing_id = str(uuid.uuid4())
        response = client.get(f"{BASE}/{missing_id}")

        assert response.status_code == 404
        assert "detail" in response.json()

    def test_invalid_wallet_id_path_returns_422(
        self,
        client: TestClient,
    ) -> None:
        response = client.get(f"{BASE}/not-a-uuid")

        assert response.status_code == 422


class TestWalletStatusTransitions:
    """POST lock / activate / close."""

    def test_lock_activate_close_cycle(
        self,
        client: TestClient,
        created_wallet: dict[str, str],
    ) -> None:
        wallet_id = created_wallet["wallet_id"]

        lock = client.post(f"{BASE}/{wallet_id}/lock")
        assert lock.status_code == 204
        assert _get_wallet(client, wallet_id)["status"] == "LOCKED"

        activate = client.post(f"{BASE}/{wallet_id}/activate")
        assert activate.status_code == 204
        assert _get_wallet(client, wallet_id)["status"] == "ACTIVE"

        close = client.post(f"{BASE}/{wallet_id}/close")
        assert close.status_code == 204
        assert _get_wallet(client, wallet_id)["status"] == "CLOSED"

    def test_status_ops_on_missing_wallet_return_404(
        self,
        client: TestClient,
    ) -> None:
        missing_id = str(uuid.uuid4())
        for action in ("lock", "activate", "close"):
            response = client.post(f"{BASE}/{missing_id}/{action}")
            assert response.status_code == 404, action


# ---------------------------------------------------------------------------
# Cash operations
# ---------------------------------------------------------------------------


class TestCashOperations:
    """Deposit, withdraw, reserve, release, settle."""

    def test_deposit_and_withdraw(
        self,
        client: TestClient,
        created_wallet: dict[str, str],
    ) -> None:
        wallet_id = created_wallet["wallet_id"]

        deposit = client.post(
            f"{BASE}/{wallet_id}/deposits",
            json={"amount": "100.00", "currency": "USD"},
        )
        assert deposit.status_code == 204

        wallet = _get_wallet(client, wallet_id)
        cash = _cash(wallet)
        assert cash is not None
        assert Decimal(str(cash["available"])) == Decimal("100.00")
        assert Decimal(str(cash["reserved"])) == Decimal("0")

        withdraw = client.post(
            f"{BASE}/{wallet_id}/withdrawals",
            json={"amount": "40.00", "currency": "USD"},
        )
        assert withdraw.status_code == 204

        wallet = _get_wallet(client, wallet_id)
        cash = _cash(wallet)
        assert cash is not None
        assert Decimal(str(cash["available"])) == Decimal("60.00")

    def test_reserve_release_and_consume(
        self,
        client: TestClient,
        created_wallet: dict[str, str],
    ) -> None:
        wallet_id = created_wallet["wallet_id"]

        client.post(
            f"{BASE}/{wallet_id}/deposits",
            json={"amount": "200.00", "currency": "USD"},
        )

        reserve = client.post(
            f"{BASE}/{wallet_id}/cash-reservations",
            json={"amount": "75.50", "currency": "USD"},
        )
        assert reserve.status_code == 204

        wallet = _get_wallet(client, wallet_id)
        cash = _cash(wallet)
        assert cash is not None
        assert Decimal(str(cash["available"])) == Decimal("124.50")
        assert Decimal(str(cash["reserved"])) == Decimal("75.50")

        release = client.post(
            f"{BASE}/{wallet_id}/cash-releases",
            json={"amount": "25.50", "currency": "USD"},
        )
        assert release.status_code == 204

        wallet = _get_wallet(client, wallet_id)
        cash = _cash(wallet)
        assert cash is not None
        assert Decimal(str(cash["available"])) == Decimal("150.00")
        assert Decimal(str(cash["reserved"])) == Decimal("50.00")

        settle = client.post(
            f"{BASE}/{wallet_id}/cash-settlements",
            json={"amount": "50.00", "currency": "USD"},
        )
        assert settle.status_code == 204

        wallet = _get_wallet(client, wallet_id)
        cash = _cash(wallet)
        assert cash is not None
        assert Decimal(str(cash["available"])) == Decimal("150.00")
        assert Decimal(str(cash["reserved"])) == Decimal("0")

    def test_cash_ops_require_active_wallet(
        self,
        client: TestClient,
        created_wallet: dict[str, str],
    ) -> None:
        wallet_id = created_wallet["wallet_id"]
        client.post(f"{BASE}/{wallet_id}/lock")

        response = client.post(
            f"{BASE}/{wallet_id}/deposits",
            json={"amount": "10.00", "currency": "USD"},
        )
        assert response.status_code == 409

    def test_withdraw_missing_balance_returns_404(
        self,
        client: TestClient,
        created_wallet: dict[str, str],
    ) -> None:
        wallet_id = created_wallet["wallet_id"]
        response = client.post(
            f"{BASE}/{wallet_id}/withdrawals",
            json={"amount": "10.00", "currency": "USD"},
        )
        assert response.status_code == 404

    def test_invalid_money_body_returns_422(
        self,
        client: TestClient,
        created_wallet: dict[str, str],
    ) -> None:
        wallet_id = created_wallet["wallet_id"]
        response = client.post(
            f"{BASE}/{wallet_id}/deposits",
            json={"amount": "-5.00", "currency": "USD"},
        )
        assert response.status_code == 422

    def test_invalid_currency_length_returns_422(
        self,
        client: TestClient,
        created_wallet: dict[str, str],
    ) -> None:
        wallet_id = created_wallet["wallet_id"]
        response = client.post(
            f"{BASE}/{wallet_id}/deposits",
            json={"amount": "10.00", "currency": "US"},
        )
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# Holding operations
# ---------------------------------------------------------------------------


class TestHoldingOperations:
    """Add, remove, reserve, release, settle holdings."""

    def test_add_and_remove_holding(
        self,
        client: TestClient,
        created_wallet: dict[str, str],
        instrument_id: str,
    ) -> None:
        wallet_id = created_wallet["wallet_id"]

        add = client.post(
            f"{BASE}/{wallet_id}/holdings",
            json={
                "instrument_id": instrument_id,
                "quantity": 10,
                "average_cost": "25.50",
                "average_cost_currency": "USD",
            },
        )
        assert add.status_code == 204

        wallet = _get_wallet(client, wallet_id)
        holding = _holding(wallet, instrument_id)
        assert holding is not None
        assert holding["available"] == 10
        assert holding["reserved"] == 0
        assert Decimal(str(holding["average_cost"])) == Decimal("25.50")
        assert holding["average_cost_currency"] == "USD"

        remove = client.post(
            f"{BASE}/{wallet_id}/holding-removals",
            json={"instrument_id": instrument_id, "quantity": 4},
        )
        assert remove.status_code == 204

        wallet = _get_wallet(client, wallet_id)
        holding = _holding(wallet, instrument_id)
        assert holding is not None
        assert holding["available"] == 6

    def test_reserve_release_and_consume_holding(
        self,
        client: TestClient,
        created_wallet: dict[str, str],
        instrument_id: str,
    ) -> None:
        wallet_id = created_wallet["wallet_id"]

        client.post(
            f"{BASE}/{wallet_id}/holdings",
            json={
                "instrument_id": instrument_id,
                "quantity": 20,
                "average_cost": "10.00",
                "average_cost_currency": "USD",
            },
        )

        reserve = client.post(
            f"{BASE}/{wallet_id}/holding-reservations",
            json={"instrument_id": instrument_id, "quantity": 8},
        )
        assert reserve.status_code == 204

        wallet = _get_wallet(client, wallet_id)
        holding = _holding(wallet, instrument_id)
        assert holding is not None
        assert holding["available"] == 12
        assert holding["reserved"] == 8

        release = client.post(
            f"{BASE}/{wallet_id}/holding-releases",
            json={"instrument_id": instrument_id, "quantity": 3},
        )
        assert release.status_code == 204

        wallet = _get_wallet(client, wallet_id)
        holding = _holding(wallet, instrument_id)
        assert holding is not None
        assert holding["available"] == 15
        assert holding["reserved"] == 5

        settle = client.post(
            f"{BASE}/{wallet_id}/holding-settlements",
            json={"instrument_id": instrument_id, "quantity": 5},
        )
        assert settle.status_code == 204

        wallet = _get_wallet(client, wallet_id)
        holding = _holding(wallet, instrument_id)
        assert holding is not None
        assert holding["available"] == 15
        assert holding["reserved"] == 0

    def test_remove_all_shares_drops_holding(
        self,
        client: TestClient,
        created_wallet: dict[str, str],
        instrument_id: str,
    ) -> None:
        wallet_id = created_wallet["wallet_id"]

        client.post(
            f"{BASE}/{wallet_id}/holdings",
            json={
                "instrument_id": instrument_id,
                "quantity": 5,
                "average_cost": "1.00",
                "average_cost_currency": "USD",
            },
        )
        client.post(
            f"{BASE}/{wallet_id}/holding-removals",
            json={"instrument_id": instrument_id, "quantity": 5},
        )

        wallet = _get_wallet(client, wallet_id)
        assert _holding(wallet, instrument_id) is None

    def test_holding_ops_require_active_wallet(
        self,
        client: TestClient,
        created_wallet: dict[str, str],
        instrument_id: str,
    ) -> None:
        wallet_id = created_wallet["wallet_id"]
        client.post(f"{BASE}/{wallet_id}/lock")

        response = client.post(
            f"{BASE}/{wallet_id}/holdings",
            json={
                "instrument_id": instrument_id,
                "quantity": 1,
                "average_cost": "1.00",
                "average_cost_currency": "USD",
            },
        )
        assert response.status_code == 409

    def test_missing_holding_returns_404(
        self,
        client: TestClient,
        created_wallet: dict[str, str],
        instrument_id: str,
    ) -> None:
        wallet_id = created_wallet["wallet_id"]
        response = client.post(
            f"{BASE}/{wallet_id}/holding-removals",
            json={"instrument_id": instrument_id, "quantity": 1},
        )
        assert response.status_code == 404

    def test_invalid_quantity_returns_422(
        self,
        client: TestClient,
        created_wallet: dict[str, str],
        instrument_id: str,
    ) -> None:
        wallet_id = created_wallet["wallet_id"]
        response = client.post(
            f"{BASE}/{wallet_id}/holdings",
            json={
                "instrument_id": instrument_id,
                "quantity": 0,
                "average_cost": "1.00",
                "average_cost_currency": "USD",
            },
        )
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# Full happy-path journey
# ---------------------------------------------------------------------------


class TestFullWalletJourney:
    """Single scenario that exercises the main trading lifecycle."""

    def test_buy_and_sell_settlement_flow(
        self,
        client: TestClient,
        trader_id: str,
        instrument_id: str,
    ) -> None:
        # 1. Open wallet
        create = client.post(BASE, json={"trader_id": trader_id})
        assert create.status_code == 201
        wallet_id = create.json()["wallet_id"]

        # 2. Fund with cash
        assert (
            client.post(
                f"{BASE}/{wallet_id}/deposits",
                json={"amount": "1000.00", "currency": "USD"},
            ).status_code
            == 204
        )

        # 3. Reserve cash for a buy order
        assert (
            client.post(
                f"{BASE}/{wallet_id}/cash-reservations",
                json={"amount": "255.00", "currency": "USD"},
            ).status_code
            == 204
        )

        # 4. Settle buy: consume reserved cash, credit shares
        assert (
            client.post(
                f"{BASE}/{wallet_id}/cash-settlements",
                json={"amount": "255.00", "currency": "USD"},
            ).status_code
            == 204
        )
        assert (
            client.post(
                f"{BASE}/{wallet_id}/holdings",
                json={
                    "instrument_id": instrument_id,
                    "quantity": 10,
                    "average_cost": "25.50",
                    "average_cost_currency": "USD",
                },
            ).status_code
            == 204
        )

        wallet = _get_wallet(client, wallet_id)
        cash = _cash(wallet)
        holding = _holding(wallet, instrument_id)
        assert cash is not None
        assert Decimal(str(cash["available"])) == Decimal("745.00")
        assert Decimal(str(cash["reserved"])) == Decimal("0")
        assert holding is not None
        assert holding["available"] == 10

        # 5. Reserve shares for a sell order
        assert (
            client.post(
                f"{BASE}/{wallet_id}/holding-reservations",
                json={"instrument_id": instrument_id, "quantity": 4},
            ).status_code
            == 204
        )

        # 6. Settle sell: consume reserved shares, credit cash
        assert (
            client.post(
                f"{BASE}/{wallet_id}/holding-settlements",
                json={"instrument_id": instrument_id, "quantity": 4},
            ).status_code
            == 204
        )
        assert (
            client.post(
                f"{BASE}/{wallet_id}/deposits",
                json={"amount": "120.00", "currency": "USD"},
            ).status_code
            == 204
        )

        wallet = _get_wallet(client, wallet_id)
        cash = _cash(wallet)
        holding = _holding(wallet, instrument_id)
        assert cash is not None
        assert Decimal(str(cash["available"])) == Decimal("865.00")
        assert holding is not None
        assert holding["available"] == 6
        assert holding["reserved"] == 0

        # 7. Close wallet
        assert client.post(f"{BASE}/{wallet_id}/close").status_code == 204
        assert _get_wallet(client, wallet_id)["status"] == "CLOSED"
