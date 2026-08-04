from decimal import Decimal

import httpx

from src.domain.ports.wallet_gateway import WalletGateway
from src.exceptions import (
    InsufficientFundsError,
    InsufficientHoldingsError,
    WalletIntegrationError,
)


class HttpWalletGateway(WalletGateway):
    """HTTP adapter for Wallet Service reserve/release APIs."""

    def __init__(self, base_url: str, timeout: float = 5.0) -> None:
        self._base = base_url.rstrip("/")
        self._timeout = timeout

    async def reserve_for_buy(
        self,
        trader_id: str,
        amount: Decimal,
        currency: str,
    ) -> None:
        wallet_id = await self._wallet_id_for_trader(trader_id)
        await self._post(
            f"/api/v1/wallets/{wallet_id}/cash-reservations",
            {"amount": str(amount), "currency": currency},
            insufficient_cls=InsufficientFundsError,
        )

    async def reserve_for_sell(
        self,
        trader_id: str,
        instrument_id: str,
        quantity: int,
    ) -> None:
        wallet_id = await self._wallet_id_for_trader(trader_id)
        await self._post(
            f"/api/v1/wallets/{wallet_id}/holding-reservations",
            {"instrument_id": instrument_id, "quantity": quantity},
            insufficient_cls=InsufficientHoldingsError,
        )

    async def release_buy_reservation(
        self,
        trader_id: str,
        amount: Decimal,
        currency: str,
    ) -> None:
        wallet_id = await self._wallet_id_for_trader(trader_id)
        await self._post(
            f"/api/v1/wallets/{wallet_id}/cash-releases",
            {"amount": str(amount), "currency": currency},
            insufficient_cls=WalletIntegrationError,
        )

    async def release_sell_reservation(
        self,
        trader_id: str,
        instrument_id: str,
        quantity: int,
    ) -> None:
        wallet_id = await self._wallet_id_for_trader(trader_id)
        await self._post(
            f"/api/v1/wallets/{wallet_id}/holding-releases",
            {"instrument_id": instrument_id, "quantity": quantity},
            insufficient_cls=WalletIntegrationError,
        )

    async def _wallet_id_for_trader(self, trader_id: str) -> str:
        url = f"{self._base}/api/v1/wallets/by-trader/{trader_id}"
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(url)
        except Exception as exc:
            raise WalletIntegrationError(
                f"Failed to resolve wallet for trader '{trader_id}': {exc}"
            ) from exc

        if response.status_code == 404:
            raise WalletIntegrationError(f"No wallet found for trader '{trader_id}'.")
        if response.status_code >= 400:
            raise WalletIntegrationError(
                f"Wallet lookup failed ({response.status_code}): {response.text}"
            )
        return response.json()["wallet_id"]

    async def _post(
        self,
        path: str,
        body: dict,
        *,
        insufficient_cls: type[Exception],
    ) -> None:
        url = f"{self._base}{path}"
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(url, json=body)
        except Exception as exc:
            raise WalletIntegrationError(f"Wallet request failed: {exc}") from exc

        if response.status_code in (409, 422):
            raise insufficient_cls(response.text)
        if response.status_code >= 400:
            raise WalletIntegrationError(
                f"Wallet request failed ({response.status_code}): {response.text}"
            )
