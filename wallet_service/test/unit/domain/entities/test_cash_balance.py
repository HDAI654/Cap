import pytest
from decimal import Decimal
from src.domain.entities.cash_balance import CashBalance
from src.domain.value_objects.currency import Currency
from src.domain.value_objects.money import Money
from src.exceptions import (
    InvalidMoneyAmountError,
    CurrencyMismatchError,
)


class TestCashBalance:
    def test_valid_cash_balance_creation(self):
        currency = Currency.USD
        available = Money("100.00", currency)
        reserved = Money("50.00", currency)

        cash_balance = CashBalance(currency, available, reserved)

        assert cash_balance.currency == currency
        assert cash_balance.available == available
        assert cash_balance.reserved == reserved

    def test_cash_balance_creation_with_zero_balances(self):
        currency = Currency.EUR
        available = Money("0.00", currency)
        reserved = Money("0.00", currency)

        cash_balance = CashBalance(currency, available, reserved)

        assert cash_balance.available.amount == Decimal("0.00")
        assert cash_balance.reserved.amount == Decimal("0.00")

    def test_cash_balance_creation_with_currency_mismatch_available(self):
        currency = Currency.USD
        available = Money("100.00", Currency.EUR)
        reserved = Money("50.00", currency)

        with pytest.raises(CurrencyMismatchError):
            CashBalance(currency, available, reserved)

    def test_cash_balance_creation_with_currency_mismatch_reserved(self):
        currency = Currency.USD
        available = Money("100.00", currency)
        reserved = Money("50.00", Currency.EUR)

        with pytest.raises(CurrencyMismatchError):
            CashBalance(currency, available, reserved)

    def test_deposit_valid(self):
        currency = Currency.USD
        cash_balance = CashBalance(
            currency, Money("100.00", currency), Money("50.00", currency)
        )

        deposit_amount = Money("25.00", currency)
        cash_balance.deposit(deposit_amount)

        assert cash_balance.available == Money("125.00", currency)
        assert cash_balance.reserved == Money("50.00", currency)

    def test_deposit_zero_amount(self):
        currency = Currency.USD
        cash_balance = CashBalance(
            currency, Money("100.00", currency), Money("50.00", currency)
        )

        deposit_amount = Money("0.00", currency)
        cash_balance.deposit(deposit_amount)

        assert cash_balance.available == Money("100.00", currency)
        assert cash_balance.reserved == Money("50.00", currency)

    def test_deposit_invalid_currency(self):
        currency = Currency.USD
        cash_balance = CashBalance(
            currency, Money("100.00", currency), Money("50.00", currency)
        )

        deposit_amount = Money("25.00", Currency.EUR)

        with pytest.raises(CurrencyMismatchError):
            cash_balance.deposit(deposit_amount)

    def test_withdraw_valid(self):
        currency = Currency.USD
        cash_balance = CashBalance(
            currency, Money("100.00", currency), Money("50.00", currency)
        )

        withdraw_amount = Money("30.00", currency)
        cash_balance.withdraw(withdraw_amount)

        assert cash_balance.available == Money("70.00", currency)
        assert cash_balance.reserved == Money("50.00", currency)

    def test_withdraw_insufficient_balance(self):
        currency = Currency.USD
        cash_balance = CashBalance(
            currency, Money("100.00", currency), Money("50.00", currency)
        )

        withdraw_amount = Money("150.00", currency)

        with pytest.raises(InvalidMoneyAmountError):
            cash_balance.withdraw(withdraw_amount)

    def test_withdraw_exact_balance(self):
        currency = Currency.USD
        cash_balance = CashBalance(
            currency, Money("100.00", currency), Money("50.00", currency)
        )

        withdraw_amount = Money("100.00", currency)
        cash_balance.withdraw(withdraw_amount)

        assert cash_balance.available == Money("0.00", currency)
        assert cash_balance.reserved == Money("50.00", currency)

    def test_withdraw_invalid_currency(self):
        currency = Currency.USD
        cash_balance = CashBalance(
            currency, Money("100.00", currency), Money("50.00", currency)
        )

        withdraw_amount = Money("30.00", Currency.EUR)

        with pytest.raises(CurrencyMismatchError):
            cash_balance.withdraw(withdraw_amount)

    def test_reserve_valid(self):
        currency = Currency.USD
        cash_balance = CashBalance(
            currency, Money("100.00", currency), Money("50.00", currency)
        )

        reserve_amount = Money("30.00", currency)
        cash_balance.reserve(reserve_amount)

        assert cash_balance.available == Money("70.00", currency)
        assert cash_balance.reserved == Money("80.00", currency)

    def test_reserve_insufficient_balance(self):
        currency = Currency.USD
        cash_balance = CashBalance(
            currency, Money("100.00", currency), Money("50.00", currency)
        )

        reserve_amount = Money("150.00", currency)

        with pytest.raises(InvalidMoneyAmountError):
            cash_balance.reserve(reserve_amount)

    def test_reserve_zero_amount(self):
        currency = Currency.USD
        cash_balance = CashBalance(
            currency, Money("100.00", currency), Money("50.00", currency)
        )

        reserve_amount = Money("0.00", currency)
        cash_balance.reserve(reserve_amount)

        assert cash_balance.available == Money("100.00", currency)
        assert cash_balance.reserved == Money("50.00", currency)

    def test_reserve_invalid_currency(self):
        currency = Currency.USD
        cash_balance = CashBalance(
            currency, Money("100.00", currency), Money("50.00", currency)
        )

        reserve_amount = Money("30.00", Currency.EUR)

        with pytest.raises(CurrencyMismatchError):
            cash_balance.reserve(reserve_amount)

    def test_release_valid(self):
        currency = Currency.USD
        cash_balance = CashBalance(
            currency, Money("100.00", currency), Money("50.00", currency)
        )

        release_amount = Money("20.00", currency)
        cash_balance.release(release_amount)

        assert cash_balance.available == Money("120.00", currency)
        assert cash_balance.reserved == Money("30.00", currency)

    def test_release_insufficient_reserved(self):
        currency = Currency.USD
        cash_balance = CashBalance(
            currency, Money("100.00", currency), Money("50.00", currency)
        )

        release_amount = Money("60.00", currency)

        with pytest.raises(InvalidMoneyAmountError):
            cash_balance.release(release_amount)

    def test_release_exact_reserved(self):
        currency = Currency.USD
        cash_balance = CashBalance(
            currency, Money("100.00", currency), Money("50.00", currency)
        )

        release_amount = Money("50.00", currency)
        cash_balance.release(release_amount)

        assert cash_balance.available == Money("150.00", currency)
        assert cash_balance.reserved == Money("0.00", currency)

    def test_release_invalid_currency(self):
        currency = Currency.USD
        cash_balance = CashBalance(
            currency, Money("100.00", currency), Money("50.00", currency)
        )

        release_amount = Money("20.00", Currency.EUR)

        with pytest.raises(CurrencyMismatchError):
            cash_balance.release(release_amount)

    def test_consume_reserved_valid(self):
        currency = Currency.USD
        cash_balance = CashBalance(
            currency, Money("100.00", currency), Money("50.00", currency)
        )

        consume_amount = Money("20.00", currency)
        cash_balance.consume_reserved(consume_amount)

        assert cash_balance.available == Money("100.00", currency)
        assert cash_balance.reserved == Money("30.00", currency)

    def test_consume_reserved_insufficient(self):
        currency = Currency.USD
        cash_balance = CashBalance(
            currency, Money("100.00", currency), Money("50.00", currency)
        )

        consume_amount = Money("60.00", currency)

        with pytest.raises(InvalidMoneyAmountError):
            cash_balance.consume_reserved(consume_amount)

    def test_consume_reserved_exact(self):
        currency = Currency.USD
        cash_balance = CashBalance(
            currency, Money("100.00", currency), Money("50.00", currency)
        )

        consume_amount = Money("50.00", currency)
        cash_balance.consume_reserved(consume_amount)

        assert cash_balance.available == Money("100.00", currency)
        assert cash_balance.reserved == Money("0.00", currency)

    def test_consume_reserved_invalid_currency(self):
        currency = Currency.USD
        cash_balance = CashBalance(
            currency, Money("100.00", currency), Money("50.00", currency)
        )

        consume_amount = Money("20.00", Currency.EUR)

        with pytest.raises(CurrencyMismatchError):
            cash_balance.consume_reserved(consume_amount)

    def test_multiple_operations_sequence(self):
        currency = Currency.USD
        cash_balance = CashBalance(
            currency, Money("100.00", currency), Money("0.00", currency)
        )

        # Deposit
        cash_balance.deposit(Money("50.00", currency))
        assert cash_balance.available == Money("150.00", currency)
        assert cash_balance.reserved == Money("0.00", currency)

        # Reserve
        cash_balance.reserve(Money("30.00", currency))
        assert cash_balance.available == Money("120.00", currency)
        assert cash_balance.reserved == Money("30.00", currency)

        # Release
        cash_balance.release(Money("10.00", currency))
        assert cash_balance.available == Money("130.00", currency)
        assert cash_balance.reserved == Money("20.00", currency)

        # Consume reserved
        cash_balance.consume_reserved(Money("20.00", currency))
        assert cash_balance.available == Money("130.00", currency)
        assert cash_balance.reserved == Money("0.00", currency)

        # Withdraw
        cash_balance.withdraw(Money("50.00", currency))
        assert cash_balance.available == Money("80.00", currency)
        assert cash_balance.reserved == Money("0.00", currency)
