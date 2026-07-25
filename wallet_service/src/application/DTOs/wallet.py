from dataclasses import dataclass
from src.application.DTOs.cash_balance import CashBalanceDTO
from src.application.DTOs.holding import HoldingDTO


@dataclass(frozen=True, slots=True)
class WalletDTO:
    """Full wallet projection returned to the presentation layer."""

    wallet_id: str
    trader_id: str
    status: str
    cash_balances: tuple[CashBalanceDTO, ...]
    holdings: tuple[HoldingDTO, ...]
