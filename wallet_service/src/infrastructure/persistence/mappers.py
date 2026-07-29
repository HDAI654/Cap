from src.domain.entities.cash_balance import CashBalance
from src.domain.entities.holding import Holding
from src.domain.entities.wallet import Wallet
from src.domain.value_objects.currency import Currency
from src.domain.value_objects.instrument_id import InstrumentId
from src.domain.value_objects.money import Money
from src.domain.value_objects.quantity import Quantity
from src.domain.value_objects.trader_id import TraderId
from src.domain.value_objects.wallet_id import WalletId
from src.domain.value_objects.wallet_status import WalletStatus
from src.infrastructure.persistence.models import (
    CashBalanceModel,
    HoldingModel,
    WalletModel,
)


def wallet_to_model(wallet: Wallet) -> WalletModel:
    """Convert a domain Wallet aggregate into a new ORM model graph."""
    model = WalletModel(
        id=wallet.id.value,
        trader_id=wallet.trader_id.value,
        status=wallet.status.value,
    )
    model.cash_balances = [
        cash_balance_to_model(wallet.id.value, balance)
        for balance in wallet.cash_balances
    ]
    model.holdings = [
        holding_to_model(wallet.id.value, holding) for holding in wallet.holdings
    ]
    return model


def cash_balance_to_model(wallet_id: str, balance: CashBalance) -> CashBalanceModel:
    """Convert a domain CashBalance into an ORM model."""
    return CashBalanceModel(
        wallet_id=wallet_id,
        currency=balance.currency.value,
        available=balance.available.amount,
        reserved=balance.reserved.amount,
    )


def holding_to_model(wallet_id: str, holding: Holding) -> HoldingModel:
    """Convert a domain Holding into an ORM model."""
    return HoldingModel(
        wallet_id=wallet_id,
        instrument_id=holding.instrument_id.value,
        available=holding.available.value,
        reserved=holding.reserved.value,
        average_cost=holding.average_cost.amount,
        average_cost_currency=holding.average_cost.currency.value,
    )


def model_to_wallet(model: WalletModel) -> Wallet:
    """Reconstitute a domain Wallet aggregate from an ORM model graph."""
    cash_balances = [model_to_cash_balance(cb) for cb in model.cash_balances]
    holdings = [model_to_holding(h) for h in model.holdings]
    return Wallet(
        id=WalletId(model.id),
        trader_id=TraderId(model.trader_id),
        status=WalletStatus(model.status),
        cash_balances=cash_balances,
        holdings=holdings,
    )


def model_to_cash_balance(model: CashBalanceModel) -> CashBalance:
    """Reconstitute a domain CashBalance from an ORM model."""
    currency = Currency(model.currency)
    return CashBalance(
        currency=currency,
        available=Money(model.available, currency),
        reserved=Money(model.reserved, currency),
    )


def model_to_holding(model: HoldingModel) -> Holding:
    """Reconstitute a domain Holding from an ORM model."""
    cost_currency = Currency(model.average_cost_currency)
    return Holding(
        instrument_id=InstrumentId(model.instrument_id),
        available=Quantity(model.available),
        reserved=Quantity(model.reserved),
        average_cost=Money(model.average_cost, cost_currency),
    )
