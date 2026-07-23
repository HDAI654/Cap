from wallet_service.src.domain.entities.wallet import Wallet
from wallet_service.src.domain.value_objects.trader_id import TraderId


class WalletFactory:
    """Factory for creating Wallet aggregates."""

    @staticmethod
    def create(trader_id: TraderId) -> Wallet:
        """Create a new wallet aggregate."""
        return Wallet.create(trader_id=trader_id)
