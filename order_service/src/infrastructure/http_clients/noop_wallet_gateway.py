from decimal import Decimal

from src.domain.ports.wallet_gateway import WalletGateway


class NoOpWalletGateway(WalletGateway):
    """No-op wallet adapter used when WALLET_INTEGRATION_ENABLED is false."""

    async def reserve_for_buy(
        self,
        trader_id: str,
        amount: Decimal,
        currency: str,
    ) -> None:
        return None

    async def reserve_for_sell(
        self,
        trader_id: str,
        instrument_id: str,
        quantity: int,
    ) -> None:
        return None

    async def release_buy_reservation(
        self,
        trader_id: str,
        amount: Decimal,
        currency: str,
    ) -> None:
        return None

    async def release_sell_reservation(
        self,
        trader_id: str,
        instrument_id: str,
        quantity: int,
    ) -> None:
        return None
