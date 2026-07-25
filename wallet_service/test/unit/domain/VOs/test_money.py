import pytest
from decimal import Decimal
from src.domain.value_objects.money import Money
from src.domain.value_objects.currency import Currency
from src.exceptions import (
    InvalidCurrencyError,
    InvalidMoneyAmountError,
    CurrencyMismatchError,
    MoneyOperationError,
)


class TestMoney:
    def test_valid_money_creation(self):
        money = Money("10.50", Currency.USD)
        assert money.amount == Decimal("10.50")
        assert money.currency == Currency.USD

    def test_money_with_integer(self):
        money = Money(10, Currency.EUR)
        assert money.amount == Decimal("10.00")
        assert money.currency == Currency.EUR

    def test_money_with_decimal(self):
        money = Money(Decimal("99.99"), Currency.USD)
        assert money.amount == Decimal("99.99")

    def test_invalid_currency(self):
        with pytest.raises(InvalidCurrencyError):
            Money("10.00", "USD")  # Not a Currency enum

    def test_invalid_amount_string(self):
        with pytest.raises(InvalidMoneyAmountError):
            Money("not a number", Currency.USD)

    def test_negative_amount(self):
        with pytest.raises(InvalidMoneyAmountError):
            Money("-10.50", Currency.USD)

    def test_more_than_two_decimal_places(self):
        with pytest.raises(InvalidMoneyAmountError):
            Money("10.555", Currency.USD)

    def test_infinite_amount(self):
        with pytest.raises(InvalidMoneyAmountError):
            Money(float("inf"), Currency.USD)

    def test_money_addition(self):
        m1 = Money("10.50", Currency.USD)
        m2 = Money("5.25", Currency.USD)
        result = m1 + m2

        assert result.amount == Decimal("15.75")
        assert result.currency == Currency.USD

    def test_money_addition_different_currencies(self):
        m1 = Money("10.50", Currency.USD)
        m2 = Money("5.25", Currency.EUR)

        with pytest.raises(CurrencyMismatchError):
            m1 + m2

    def test_money_subtraction(self):
        m1 = Money("10.50", Currency.USD)
        m2 = Money("5.25", Currency.USD)
        result = m1 - m2

        assert result.amount == Decimal("5.25")
        assert result.currency == Currency.USD

    def test_money_subtraction_negative_result(self):
        m1 = Money("5.25", Currency.USD)
        m2 = Money("10.50", Currency.USD)

        with pytest.raises(InvalidMoneyAmountError):
            m1 - m2

    def test_money_subtraction_different_currencies(self):
        m1 = Money("10.50", Currency.USD)
        m2 = Money("5.25", Currency.EUR)

        with pytest.raises(CurrencyMismatchError):
            m1 - m2

    def test_money_less_than(self):
        m1 = Money("10.50", Currency.USD)
        m2 = Money("15.25", Currency.USD)

        assert m1 < m2
        assert not (m2 < m1)

    def test_money_less_than_different_currencies(self):
        m1 = Money("10.50", Currency.USD)
        m2 = Money("15.25", Currency.EUR)

        with pytest.raises(CurrencyMismatchError):
            m1 < m2

    def test_money_less_than_or_equal(self):
        m1 = Money("10.50", Currency.USD)
        m2 = Money("10.50", Currency.USD)
        m3 = Money("15.25", Currency.USD)

        assert m1 <= m2
        assert m1 <= m3
        assert not (m3 <= m1)

    def test_money_greater_than(self):
        m1 = Money("15.25", Currency.USD)
        m2 = Money("10.50", Currency.USD)

        assert m1 > m2
        assert not (m2 > m1)

    def test_money_greater_than_or_equal(self):
        m1 = Money("10.50", Currency.USD)
        m2 = Money("10.50", Currency.USD)
        m3 = Money("15.25", Currency.USD)

        assert m1 >= m2
        assert m3 >= m1
        assert not (m1 >= m3)

    def test_money_equality(self):
        m1 = Money("10.50", Currency.USD)
        m2 = Money("10.50", Currency.USD)
        m3 = Money("15.25", Currency.USD)
        m4 = Money("10.50", Currency.EUR)

        assert m1 == m2
        assert m1 != m3
        assert m1 != m4

    def test_money_hash(self):
        m1 = Money("10.50", Currency.USD)
        m2 = Money("10.50", Currency.USD)

        assert hash(m1) == hash(m2)

    def test_money_operation_with_non_money(self):
        m = Money("10.50", Currency.USD)

        with pytest.raises(MoneyOperationError):
            m + 5

        with pytest.raises(MoneyOperationError):
            m - 5

        with pytest.raises(MoneyOperationError):
            m < 5

    def test_money_properties(self):
        m = Money("10.50", Currency.USD)

        assert m.amount == Decimal("10.50")
        assert m.currency == Currency.USD
        assert m.value == Decimal("10.50")
