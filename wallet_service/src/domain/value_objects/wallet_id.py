from shared.id_vo import ID
from src.exceptions import InvalidWalletIdError


class WalletId(ID):
    """Represents the unique identifier of a Wallet aggregate."""

    def __init__(self, value):
        super().__init__(value, InvalidWalletIdError)
