from enum import StrEnum

class Currency(StrEnum):
    """Supported trading currencies."""

    USD = "USD"
    EUR = "EUR"

    @property
    def symbol(self) -> str:
        """Return the currency symbol."""
        return {
            Currency.USD: "$",
            Currency.EUR: "€",
        }[self]