import pytest
from src.domain.entities.wallet import Wallet
from src.domain.entities.cash_balance import CashBalance
from src.domain.entities.holding import Holding
from src.domain.value_objects.wallet_status import WalletStatus
from src.domain.value_objects.currency import Currency
from src.domain.value_objects.instrument_id import InstrumentId
from src.domain.value_objects.money import Money
from src.domain.value_objects.quantity import Quantity
from src.domain.value_objects.trader_id import TraderId
from src.domain.value_objects.wallet_id import WalletId
from src.exceptions import (
    CashBalanceNotFoundError,
    CurrencyMismatchError,
    HoldingNotFoundError,
    InvalidMoneyAmountError,
    InvalidQuantityError,
)


class TestWallet:
    def test_create_wallet(self):
        trader_id = TraderId.generate()
        wallet = Wallet.create(trader_id)

        assert isinstance(wallet.id, WalletId)
        assert wallet.trader_id == trader_id
        assert wallet.status == WalletStatus.ACTIVE
        assert len(wallet.cash_balances) == 0
        assert len(wallet.holdings) == 0
        assert not wallet.is_status_changed()

    def test_wallet_initialization_with_balances_and_holdings(self):
        trader_id = TraderId.generate()
        wallet_id = WalletId.generate()
        currency = Currency.USD
        instrument_id = InstrumentId.generate()

        cash_balance = CashBalance(
            currency, Money("100.00", currency), Money("50.00", currency)
        )

        holding = Holding(
            instrument_id, Quantity(100), Quantity(50), Money("150.50", currency)
        )

        wallet = Wallet(
            id=wallet_id,
            trader_id=trader_id,
            status=WalletStatus.ACTIVE,
            cash_balances=[cash_balance],
            holdings=[holding],
        )

        assert wallet.id == wallet_id
        assert wallet.trader_id == trader_id
        assert wallet.status == WalletStatus.ACTIVE
        assert len(wallet.cash_balances) == 1
        assert len(wallet.holdings) == 1
        assert wallet.cash_balances[0] == cash_balance
        assert wallet.holdings[0] == holding

    def test_wallet_initialization_with_empty_lists(self):
        trader_id = TraderId.generate()
        wallet_id = WalletId.generate()

        wallet = Wallet(
            id=wallet_id,
            trader_id=trader_id,
            status=WalletStatus.ACTIVE,
            cash_balances=[],
            holdings=[],
        )

        assert len(wallet.cash_balances) == 0
        assert len(wallet.holdings) == 0

    def test_wallet_initialization_with_none_lists(self):
        trader_id = TraderId.generate()
        wallet_id = WalletId.generate()

        wallet = Wallet(
            id=wallet_id,
            trader_id=trader_id,
            status=WalletStatus.ACTIVE,
            cash_balances=None,
            holdings=None,
        )

        assert len(wallet.cash_balances) == 0
        assert len(wallet.holdings) == 0

    def test_deposit_cash_new_currency(self):
        trader_id = TraderId.generate()
        wallet = Wallet.create(trader_id)

        deposit_amount = Money("100.00", Currency.USD)
        wallet.deposit_cash(deposit_amount)

        assert len(wallet.cash_balances) == 1
        balance = wallet.cash_balances[0]
        assert balance.currency == Currency.USD
        assert balance.available == Money("100.00", Currency.USD)
        assert balance.reserved == Money("0.00", Currency.USD)

        created, updated = wallet.get_cash_changes()
        assert Currency.USD in created
        assert Currency.USD not in updated

    def test_deposit_cash_multiple_currencies(self):
        trader_id = TraderId.generate()
        wallet = Wallet.create(trader_id)

        wallet.deposit_cash(Money("100.00", Currency.USD))
        wallet.deposit_cash(Money("200.00", Currency.EUR))

        assert len(wallet.cash_balances) == 2

        balances = {b.currency: b for b in wallet.cash_balances}
        assert balances[Currency.USD].available == Money("100.00", Currency.USD)
        assert balances[Currency.EUR].available == Money("200.00", Currency.EUR)

        created, updated = wallet.get_cash_changes()
        assert Currency.USD in created
        assert Currency.EUR in created
        assert len(updated) == 0

    def test_deposit_cash_existing_currency(self):
        trader_id = TraderId.generate()
        wallet = Wallet.create(trader_id)

        # First deposit
        wallet.deposit_cash(Money("100.00", Currency.USD))

        # Clear changes to test updated marking
        wallet.clear_changes()

        # Second deposit
        wallet.deposit_cash(Money("50.00", Currency.USD))

        assert len(wallet.cash_balances) == 1
        balance = wallet.cash_balances[0]
        assert balance.available == Money("150.00", Currency.USD)

        created, updated = wallet.get_cash_changes()
        assert Currency.USD not in created
        assert Currency.USD in updated

    def test_withdraw_cash_valid(self):
        trader_id = TraderId.generate()
        wallet = Wallet.create(trader_id)

        wallet.deposit_cash(Money("100.00", Currency.USD))
        wallet.withdraw_cash(Money("30.00", Currency.USD))

        balance = wallet.cash_balances[0]
        assert balance.available == Money("70.00", Currency.USD)

        created, updated = wallet.get_cash_changes()
        assert Currency.USD in created
        assert Currency.USD not in updated

    def test_withdraw_cash_insufficient(self):
        trader_id = TraderId.generate()
        wallet = Wallet.create(trader_id)

        wallet.deposit_cash(Money("100.00", Currency.USD))

        with pytest.raises(InvalidMoneyAmountError):
            wallet.withdraw_cash(Money("150.00", Currency.USD))

    def test_withdraw_cash_no_balance(self):
        trader_id = TraderId.generate()
        wallet = Wallet.create(trader_id)

        with pytest.raises(CashBalanceNotFoundError):
            wallet.withdraw_cash(Money("100.00", Currency.USD))

    def test_withdraw_cash_exact_balance(self):
        trader_id = TraderId.generate()
        wallet = Wallet.create(trader_id)

        wallet.deposit_cash(Money("100.00", Currency.USD))
        wallet.withdraw_cash(Money("100.00", Currency.USD))

        balance = wallet.cash_balances[0]
        assert balance.available == Money("0.00", Currency.USD)

    def test_reserve_cash_valid(self):
        trader_id = TraderId.generate()
        wallet = Wallet.create(trader_id)

        wallet.deposit_cash(Money("100.00", Currency.USD))
        wallet.reserve_cash(Money("30.00", Currency.USD))

        balance = wallet.cash_balances[0]
        assert balance.available == Money("70.00", Currency.USD)
        assert balance.reserved == Money("30.00", Currency.USD)

    def test_reserve_cash_insufficient(self):
        trader_id = TraderId.generate()
        wallet = Wallet.create(trader_id)

        wallet.deposit_cash(Money("100.00", Currency.USD))

        with pytest.raises(InvalidMoneyAmountError):
            wallet.reserve_cash(Money("150.00", Currency.USD))

    def test_reserve_cash_no_balance(self):
        trader_id = TraderId.generate()
        wallet = Wallet.create(trader_id)

        with pytest.raises(CashBalanceNotFoundError):
            wallet.reserve_cash(Money("100.00", Currency.USD))

    def test_release_cash_valid(self):
        trader_id = TraderId.generate()
        wallet = Wallet.create(trader_id)

        wallet.deposit_cash(Money("100.00", Currency.USD))
        wallet.reserve_cash(Money("30.00", Currency.USD))
        wallet.release_cash(Money("10.00", Currency.USD))

        balance = wallet.cash_balances[0]
        assert balance.available == Money("80.00", Currency.USD)
        assert balance.reserved == Money("20.00", Currency.USD)

    def test_release_cash_insufficient_reserved(self):
        trader_id = TraderId.generate()
        wallet = Wallet.create(trader_id)

        wallet.deposit_cash(Money("100.00", Currency.USD))
        wallet.reserve_cash(Money("30.00", Currency.USD))

        with pytest.raises(InvalidMoneyAmountError):
            wallet.release_cash(Money("40.00", Currency.USD))

    def test_consume_reserved_cash_valid(self):
        trader_id = TraderId.generate()
        wallet = Wallet.create(trader_id)

        wallet.deposit_cash(Money("100.00", Currency.USD))
        wallet.reserve_cash(Money("30.00", Currency.USD))
        wallet.consume_reserved_cash(Money("20.00", Currency.USD))

        balance = wallet.cash_balances[0]
        assert balance.available == Money("70.00", Currency.USD)
        assert balance.reserved == Money("10.00", Currency.USD)

    def test_consume_reserved_cash_insufficient(self):
        trader_id = TraderId.generate()
        wallet = Wallet.create(trader_id)

        wallet.deposit_cash(Money("100.00", Currency.USD))
        wallet.reserve_cash(Money("30.00", Currency.USD))

        with pytest.raises(InvalidMoneyAmountError):
            wallet.consume_reserved_cash(Money("40.00", Currency.USD))

    def test_add_holding_new(self):
        trader_id = TraderId.generate()
        wallet = Wallet.create(trader_id)

        instrument_id = InstrumentId.generate()
        wallet.add_holding(instrument_id, Quantity(100), Money("150.50", Currency.USD))

        assert len(wallet.holdings) == 1
        holding = wallet.holdings[0]
        assert holding.instrument_id == instrument_id
        assert holding.available == Quantity(100)
        assert holding.reserved == Quantity(0)
        assert holding.average_cost == Money("150.50", Currency.USD)

        created, updated, removed = wallet.get_holding_changes()
        assert instrument_id in created
        assert instrument_id not in updated
        assert instrument_id not in removed

    def test_add_holding_multiple_instruments(self):
        trader_id = TraderId.generate()
        wallet = Wallet.create(trader_id)

        instrument_id1 = InstrumentId.generate()
        instrument_id2 = InstrumentId.generate()

        wallet.add_holding(instrument_id1, Quantity(100), Money("150.50", Currency.USD))
        wallet.add_holding(instrument_id2, Quantity(200), Money("250.75", Currency.USD))

        assert len(wallet.holdings) == 2

        created, updated, removed = wallet.get_holding_changes()
        assert instrument_id1 in created
        assert instrument_id2 in created
        assert len(updated) == 0
        assert len(removed) == 0

    def test_add_holding_existing(self):
        trader_id = TraderId.generate()
        wallet = Wallet.create(trader_id)

        instrument_id = InstrumentId.generate()

        # First add
        wallet.add_holding(instrument_id, Quantity(100), Money("150.50", Currency.USD))

        # Clear changes
        wallet.clear_changes()

        # Second add
        wallet.add_holding(instrument_id, Quantity(50), Money("152.75", Currency.USD))

        assert len(wallet.holdings) == 1
        holding = wallet.holdings[0]
        assert holding.available == Quantity(150)
        assert holding.average_cost == Money("152.75", Currency.USD)

        created, updated, removed = wallet.get_holding_changes()
        assert instrument_id not in created
        assert instrument_id in updated
        assert instrument_id not in removed

    def test_add_holding_different_currency(self):
        trader_id = TraderId.generate()
        wallet = Wallet.create(trader_id)

        instrument_id = InstrumentId.generate()

        wallet.add_holding(instrument_id, Quantity(100), Money("150.50", Currency.USD))

        # Add more with different currency should fail
        with pytest.raises(CurrencyMismatchError):
            wallet.add_holding(
                instrument_id, Quantity(50), Money("152.75", Currency.EUR)
            )

    def test_remove_holding_valid(self):
        trader_id = TraderId.generate()
        wallet = Wallet.create(trader_id)

        instrument_id = InstrumentId.generate()
        wallet.add_holding(instrument_id, Quantity(100), Money("150.50", Currency.USD))

        # Clear changes
        wallet.clear_changes()

        wallet.remove_holding(instrument_id, Quantity(40))

        assert len(wallet.holdings) == 1
        holding = wallet.holdings[0]
        assert holding.available == Quantity(60)
        assert holding.reserved == Quantity(0)

        created, updated, removed = wallet.get_holding_changes()
        assert instrument_id not in created
        assert instrument_id in updated
        assert instrument_id not in removed

    def test_remove_holding_remove_completely(self):
        trader_id = TraderId.generate()
        wallet = Wallet.create(trader_id)

        instrument_id = InstrumentId.generate()
        wallet.add_holding(instrument_id, Quantity(100), Money("150.50", Currency.USD))

        # Clear changes
        wallet.clear_changes()

        wallet.remove_holding(instrument_id, Quantity(100))

        assert len(wallet.holdings) == 0

        created, updated, removed = wallet.get_holding_changes()
        assert instrument_id not in created
        assert instrument_id not in updated
        assert instrument_id in removed

    def test_remove_holding_with_reserved_quantity(self):
        trader_id = TraderId.generate()
        wallet = Wallet.create(trader_id)

        instrument_id = InstrumentId.generate()
        wallet.add_holding(instrument_id, Quantity(100), Money("150.50", Currency.USD))
        wallet.reserve_holding(instrument_id, Quantity(30))

        # Try to remove all available, should only remove available
        wallet.remove_holding(instrument_id, Quantity(70))

        assert len(wallet.holdings) == 1
        holding = wallet.holdings[0]
        assert holding.available == Quantity(0)
        assert holding.reserved == Quantity(30)

    def test_remove_holding_insufficient(self):
        trader_id = TraderId.generate()
        wallet = Wallet.create(trader_id)

        instrument_id = InstrumentId.generate()
        wallet.add_holding(instrument_id, Quantity(100), Money("150.50", Currency.USD))

        with pytest.raises(InvalidQuantityError):
            wallet.remove_holding(instrument_id, Quantity(150))

    def test_remove_holding_not_found(self):
        trader_id = TraderId.generate()
        wallet = Wallet.create(trader_id)

        instrument_id = InstrumentId.generate()

        with pytest.raises(HoldingNotFoundError):
            wallet.remove_holding(instrument_id, Quantity(100))

    def test_reserve_holding_valid(self):
        trader_id = TraderId.generate()
        wallet = Wallet.create(trader_id)

        instrument_id = InstrumentId.generate()
        wallet.add_holding(instrument_id, Quantity(100), Money("150.50", Currency.USD))

        # Clear changes
        wallet.clear_changes()

        wallet.reserve_holding(instrument_id, Quantity(30))

        holding = wallet.holdings[0]
        assert holding.available == Quantity(70)
        assert holding.reserved == Quantity(30)

        created, updated, removed = wallet.get_holding_changes()
        assert instrument_id not in created
        assert instrument_id in updated
        assert instrument_id not in removed

    def test_reserve_holding_insufficient(self):
        trader_id = TraderId.generate()
        wallet = Wallet.create(trader_id)

        instrument_id = InstrumentId.generate()
        wallet.add_holding(instrument_id, Quantity(100), Money("150.50", Currency.USD))

        with pytest.raises(InvalidQuantityError):
            wallet.reserve_holding(instrument_id, Quantity(150))

    def test_reserve_holding_not_found(self):
        trader_id = TraderId.generate()
        wallet = Wallet.create(trader_id)

        instrument_id = InstrumentId.generate()

        with pytest.raises(HoldingNotFoundError):
            wallet.reserve_holding(instrument_id, Quantity(100))

    def test_release_holding_valid(self):
        trader_id = TraderId.generate()
        wallet = Wallet.create(trader_id)

        instrument_id = InstrumentId.generate()
        wallet.add_holding(instrument_id, Quantity(100), Money("150.50", Currency.USD))
        wallet.reserve_holding(instrument_id, Quantity(30))

        # Clear changes
        wallet.clear_changes()

        wallet.release_holding(instrument_id, Quantity(10))

        holding = wallet.holdings[0]
        assert holding.available == Quantity(80)
        assert holding.reserved == Quantity(20)

        created, updated, removed = wallet.get_holding_changes()
        assert instrument_id not in created
        assert instrument_id in updated
        assert instrument_id not in removed

    def test_release_holding_insufficient_reserved(self):
        trader_id = TraderId.generate()
        wallet = Wallet.create(trader_id)

        instrument_id = InstrumentId.generate()
        wallet.add_holding(instrument_id, Quantity(100), Money("150.50", Currency.USD))
        wallet.reserve_holding(instrument_id, Quantity(30))

        with pytest.raises(InvalidQuantityError):
            wallet.release_holding(instrument_id, Quantity(40))

    def test_consume_reserved_holding_valid(self):
        trader_id = TraderId.generate()
        wallet = Wallet.create(trader_id)

        instrument_id = InstrumentId.generate()
        wallet.add_holding(instrument_id, Quantity(100), Money("150.50", Currency.USD))
        wallet.reserve_holding(instrument_id, Quantity(30))

        # Clear changes
        wallet.clear_changes()

        wallet.consume_reserved_holding(instrument_id, Quantity(20))

        holding = wallet.holdings[0]
        assert holding.available == Quantity(70)
        assert holding.reserved == Quantity(10)

        created, updated, removed = wallet.get_holding_changes()
        assert instrument_id not in created
        assert instrument_id in updated
        assert instrument_id not in removed

    def test_consume_reserved_holding_insufficient(self):
        trader_id = TraderId.generate()
        wallet = Wallet.create(trader_id)

        instrument_id = InstrumentId.generate()
        wallet.add_holding(instrument_id, Quantity(100), Money("150.50", Currency.USD))
        wallet.reserve_holding(instrument_id, Quantity(30))

        with pytest.raises(InvalidQuantityError):
            wallet.consume_reserved_holding(instrument_id, Quantity(40))

    def test_lock_wallet(self):
        trader_id = TraderId.generate()
        wallet = Wallet.create(trader_id)

        assert not wallet.is_status_changed()

        wallet.lock()

        assert wallet.status == WalletStatus.LOCKED
        assert wallet.is_status_changed()

    def test_activate_wallet(self):
        trader_id = TraderId.generate()
        wallet = Wallet.create(trader_id)

        wallet.lock()
        wallet.clear_changes()

        wallet.activate()

        assert wallet.status == WalletStatus.ACTIVE
        assert wallet.is_status_changed()

    def test_close_wallet(self):
        trader_id = TraderId.generate()
        wallet = Wallet.create(trader_id)

        wallet.close()

        assert wallet.status == WalletStatus.CLOSED
        assert wallet.is_status_changed()

    def test_get_cash_changes_created_only(self):
        trader_id = TraderId.generate()
        wallet = Wallet.create(trader_id)

        wallet.deposit_cash(Money("100.00", Currency.USD))

        created, updated = wallet.get_cash_changes()
        assert Currency.USD in created
        assert Currency.USD not in updated

    def test_get_cash_changes_updated_only(self):
        trader_id = TraderId.generate()
        wallet = Wallet.create(trader_id)

        wallet.deposit_cash(Money("100.00", Currency.USD))
        wallet.clear_changes()

        wallet.deposit_cash(Money("50.00", Currency.USD))

        created, updated = wallet.get_cash_changes()
        assert Currency.USD not in created
        assert Currency.USD in updated

    def test_get_cash_changes_multiple_currencies(self):
        trader_id = TraderId.generate()
        wallet = Wallet.create(trader_id)

        # Create USD
        wallet.deposit_cash(Money("100.00", Currency.USD))

        # Create EUR
        wallet.deposit_cash(Money("200.00", Currency.EUR))

        wallet.clear_changes()

        # Update both
        wallet.deposit_cash(Money("50.00", Currency.USD))
        wallet.deposit_cash(Money("100.00", Currency.EUR))

        created, updated = wallet.get_cash_changes()
        assert Currency.USD not in created
        assert Currency.EUR not in created
        assert Currency.USD in updated
        assert Currency.EUR in updated

    def test_get_holding_changes_created_only(self):
        trader_id = TraderId.generate()
        wallet = Wallet.create(trader_id)

        instrument_id = InstrumentId.generate()
        wallet.add_holding(instrument_id, Quantity(100), Money("150.50", Currency.USD))

        created, updated, removed = wallet.get_holding_changes()
        assert instrument_id in created
        assert instrument_id not in updated
        assert instrument_id not in removed

    def test_get_holding_changes_updated_only(self):
        trader_id = TraderId.generate()
        wallet = Wallet.create(trader_id)

        instrument_id = InstrumentId.generate()
        wallet.add_holding(instrument_id, Quantity(100), Money("150.50", Currency.USD))
        wallet.clear_changes()

        wallet.add_holding(instrument_id, Quantity(50), Money("152.75", Currency.USD))

        created, updated, removed = wallet.get_holding_changes()
        assert instrument_id not in created
        assert instrument_id in updated
        assert instrument_id not in removed

    def test_get_holding_changes_removed_only(self):
        trader_id = TraderId.generate()
        wallet = Wallet.create(trader_id)

        instrument_id = InstrumentId.generate()
        wallet.add_holding(instrument_id, Quantity(100), Money("150.50", Currency.USD))
        wallet.clear_changes()

        wallet.remove_holding(instrument_id, Quantity(100))

        created, updated, removed = wallet.get_holding_changes()
        assert instrument_id not in created
        assert instrument_id not in updated
        assert instrument_id in removed

    def test_clear_changes(self):
        trader_id = TraderId.generate()
        wallet = Wallet.create(trader_id)

        wallet.deposit_cash(Money("100.00", Currency.USD))

        instrument_id = InstrumentId.generate()
        wallet.add_holding(instrument_id, Quantity(100), Money("150.50", Currency.USD))

        wallet.lock()

        # Verify changes exist
        created, updated = wallet.get_cash_changes()
        assert len(created) == 1
        assert len(updated) == 0

        created_h, updated_h, removed_h = wallet.get_holding_changes()
        assert len(created_h) == 1
        assert len(updated_h) == 0
        assert len(removed_h) == 0

        assert wallet.is_status_changed()

        # Clear changes
        wallet.clear_changes()

        created, updated = wallet.get_cash_changes()
        assert len(created) == 0
        assert len(updated) == 0

        created_h, updated_h, removed_h = wallet.get_holding_changes()
        assert len(created_h) == 0
        assert len(updated_h) == 0
        assert len(removed_h) == 0

        assert not wallet.is_status_changed()

    def test_complex_operations_sequence(self):
        trader_id = TraderId.generate()
        wallet = Wallet.create(trader_id)

        # Cash operations
        wallet.deposit_cash(Money("1000.00", Currency.USD))
        wallet.deposit_cash(Money("500.00", Currency.EUR))

        wallet.reserve_cash(Money("200.00", Currency.USD))
        wallet.consume_reserved_cash(Money("200.00", Currency.USD))

        # Holding operations
        instrument_id1 = InstrumentId.generate()
        instrument_id2 = InstrumentId.generate()

        wallet.add_holding(instrument_id1, Quantity(100), Money("150.50", Currency.USD))
        wallet.add_holding(instrument_id2, Quantity(50), Money("200.75", Currency.USD))

        wallet.reserve_holding(instrument_id1, Quantity(30))
        wallet.consume_reserved_holding(instrument_id1, Quantity(20))

        # Verify cash balances
        usd_balance = wallet.cash_balances[0]
        eur_balance = wallet.cash_balances[1]

        assert usd_balance.available == Money("800.00", Currency.USD)
        assert usd_balance.reserved == Money("0.00", Currency.USD)
        assert eur_balance.available == Money("500.00", Currency.EUR)
        assert eur_balance.reserved == Money("0.00", Currency.EUR)

        # Verify holdings
        assert len(wallet.holdings) == 2
        holdings_dict = {h.instrument_id: h for h in wallet.holdings}

        holding1 = holdings_dict[instrument_id1]
        assert holding1.available == Quantity(70)
        assert holding1.reserved == Quantity(10)

        holding2 = holdings_dict[instrument_id2]
        assert holding2.available == Quantity(50)
        assert holding2.reserved == Quantity(0)

        # Verify changes
        created_cash, updated_cash = wallet.get_cash_changes()
        assert Currency.USD in created_cash
        assert Currency.EUR in created_cash
        assert len(updated_cash) == 0

        created_h, updated_h, removed_h = wallet.get_holding_changes()
        assert instrument_id1 in created_h
        assert instrument_id2 in created_h
        assert len(updated_h) == 0
        assert len(removed_h) == 0

    def test_wallet_status_transitions(self):
        trader_id = TraderId.generate()
        wallet = Wallet.create(trader_id)

        assert wallet.status == WalletStatus.ACTIVE

        wallet.lock()
        assert wallet.status == WalletStatus.LOCKED

        wallet.activate()
        assert wallet.status == WalletStatus.ACTIVE

        wallet.close()
        assert wallet.status == WalletStatus.CLOSED

        # Can still change status after closed
        wallet.activate()
        assert wallet.status == WalletStatus.ACTIVE
