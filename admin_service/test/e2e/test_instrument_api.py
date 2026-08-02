import uuid

from fastapi.testclient import TestClient

BASE = "/api/v1/instruments"


class TestAuth:
    def test_missing_token_returns_401(
        self, client: TestClient, instrument_payload: dict
    ) -> None:
        response = client.post(BASE, json=instrument_payload)
        assert response.status_code == 401

    def test_non_admin_role_returns_403(
        self,
        client: TestClient,
        trader_headers: dict[str, str],
        instrument_payload: dict,
    ) -> None:
        response = client.post(BASE, json=instrument_payload, headers=trader_headers)
        assert response.status_code == 403

    def test_expired_token_returns_401(
        self,
        client: TestClient,
        instrument_payload: dict,
        expired_admin_headers: dict[str, str],
    ) -> None:
        response = client.post(
            BASE, json=instrument_payload, headers=expired_admin_headers
        )
        assert response.status_code == 401


class TestCreateAndGet:
    def test_create_and_get(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
        instrument_payload: dict,
    ) -> None:
        created = client.post(BASE, json=instrument_payload, headers=admin_headers)
        assert created.status_code == 201
        instrument_id = created.json()["instrument_id"]
        uuid.UUID(instrument_id, version=4)

        got = client.get(f"{BASE}/{instrument_id}", headers=admin_headers)
        assert got.status_code == 200
        body = got.json()
        assert body["symbol"] == "AAPL"
        assert body["status"] == "PENDING"
        assert body["total_shares"] == 0

    def test_duplicate_symbol_returns_409(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
        instrument_payload: dict,
    ) -> None:
        assert (
            client.post(
                BASE, json=instrument_payload, headers=admin_headers
            ).status_code
            == 201
        )
        second = client.post(BASE, json=instrument_payload, headers=admin_headers)
        assert second.status_code == 409


class TestLifecycleAndAllocation:
    def test_activate_halt_allocate(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
        instrument_payload: dict,
    ) -> None:
        instrument_id = client.post(
            BASE, json=instrument_payload, headers=admin_headers
        ).json()["instrument_id"]

        assert (
            client.post(
                f"{BASE}/{instrument_id}/activate", headers=admin_headers
            ).status_code
            == 204
        )
        assert (
            client.get(f"{BASE}/{instrument_id}", headers=admin_headers).json()[
                "status"
            ]
            == "ACTIVE"
        )

        assert (
            client.post(
                f"{BASE}/{instrument_id}/halt", headers=admin_headers
            ).status_code
            == 204
        )
        assert (
            client.get(f"{BASE}/{instrument_id}", headers=admin_headers).json()[
                "status"
            ]
            == "HALTED"
        )

        client.post(f"{BASE}/{instrument_id}/activate", headers=admin_headers)
        assert (
            client.post(
                f"{BASE}/{instrument_id}/allocations",
                json={"quantity": 1000},
                headers=admin_headers,
            ).status_code
            == 204
        )
        body = client.get(f"{BASE}/{instrument_id}", headers=admin_headers).json()
        assert body["total_shares"] == 1000

    def test_list_instruments(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
        instrument_payload: dict,
    ) -> None:
        client.post(BASE, json=instrument_payload, headers=admin_headers)
        other = {**instrument_payload, "symbol": "MSFT", "name": "Microsoft"}
        client.post(BASE, json=other, headers=admin_headers)

        response = client.get(BASE, headers=admin_headers)
        assert response.status_code == 200
        assert len(response.json()) == 2
