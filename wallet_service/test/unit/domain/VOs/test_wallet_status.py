import pytest
from src.domain.value_objects.wallet_status import WalletStatus


class TestWalletStatus:
    def test_wallet_status_values(self):
        assert WalletStatus.ACTIVE == "ACTIVE"
        assert WalletStatus.LOCKED == "LOCKED"
        assert WalletStatus.CLOSED == "CLOSED"

    def test_wallet_status_from_string(self):
        assert WalletStatus("ACTIVE") == WalletStatus.ACTIVE
        assert WalletStatus("LOCKED") == WalletStatus.LOCKED
        assert WalletStatus("CLOSED") == WalletStatus.CLOSED

    def test_invalid_wallet_status(self):
        with pytest.raises(ValueError):
            WalletStatus("INVALID")
