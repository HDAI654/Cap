import pytest
from wallet_service.src.domain.value_objects.currency import Currency


class TestCurrency:
    def test_currency_values(self):
        assert Currency.USD == "USD"
        assert Currency.EUR == "EUR"

    def test_currency_symbol(self):
        assert Currency.USD.symbol == "$"
        assert Currency.EUR.symbol == "€"

    def test_currency_from_string(self):
        assert Currency("USD") == Currency.USD
        assert Currency("EUR") == Currency.EUR

    def test_invalid_currency(self):
        with pytest.raises(ValueError):
            Currency("GBP")
