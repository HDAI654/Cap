import pytest
from src.domain.entities.holding import Holding
from src.domain.value_objects.instrument_id import InstrumentId
from src.domain.value_objects.currency import Currency
from src.domain.value_objects.money import Money
from src.domain.value_objects.quantity import Quantity
from src.exceptions import (
    InvalidQuantityError,
    CurrencyMismatchError,
)


class TestHolding:
    def test_valid_holding_creation(self):
        instrument_id = InstrumentId.generate()
        available = Quantity(100)
        reserved = Quantity(50)
        average_cost = Money("150.50", Currency.USD)

        holding = Holding(instrument_id, available, reserved, average_cost)

        assert holding.instrument_id == instrument_id
        assert holding.available == available
        assert holding.reserved == reserved
        assert holding.average_cost == average_cost

    def test_holding_creation_with_zero_quantities(self):
        instrument_id = InstrumentId.generate()
        available = Quantity(0)
        reserved = Quantity(0)
        average_cost = Money("0.00", Currency.USD)

        holding = Holding(instrument_id, available, reserved, average_cost)

        assert holding.available.value == 0
        assert holding.reserved.value == 0

    def test_add_quantity_valid(self):
        instrument_id = InstrumentId.generate()
        holding = Holding(
            instrument_id, Quantity(100), Quantity(50), Money("150.50", Currency.USD)
        )

        holding.add(Quantity(25))

        assert holding.available == Quantity(125)
        assert holding.reserved == Quantity(50)

    def test_add_zero_quantity(self):
        instrument_id = InstrumentId.generate()
        holding = Holding(
            instrument_id, Quantity(100), Quantity(50), Money("150.50", Currency.USD)
        )

        holding.add(Quantity(0))

        assert holding.available == Quantity(100)
        assert holding.reserved == Quantity(50)

    def test_remove_quantity_valid(self):
        instrument_id = InstrumentId.generate()
        holding = Holding(
            instrument_id, Quantity(100), Quantity(50), Money("150.50", Currency.USD)
        )

        holding.remove(Quantity(25))

        assert holding.available == Quantity(75)
        assert holding.reserved == Quantity(50)

    def test_remove_quantity_insufficient(self):
        instrument_id = InstrumentId.generate()
        holding = Holding(
            instrument_id, Quantity(100), Quantity(50), Money("150.50", Currency.USD)
        )

        with pytest.raises(
            InvalidQuantityError, match="Insufficient available quantity"
        ):
            holding.remove(Quantity(150))

    def test_remove_quantity_exact(self):
        instrument_id = InstrumentId.generate()
        holding = Holding(
            instrument_id, Quantity(100), Quantity(50), Money("150.50", Currency.USD)
        )

        holding.remove(Quantity(100))

        assert holding.available == Quantity(0)
        assert holding.reserved == Quantity(50)

    def test_reserve_valid(self):
        instrument_id = InstrumentId.generate()
        holding = Holding(
            instrument_id, Quantity(100), Quantity(50), Money("150.50", Currency.USD)
        )

        holding.reserve(Quantity(25))

        assert holding.available == Quantity(75)
        assert holding.reserved == Quantity(75)

    def test_reserve_insufficient_available(self):
        instrument_id = InstrumentId.generate()
        holding = Holding(
            instrument_id, Quantity(100), Quantity(50), Money("150.50", Currency.USD)
        )

        with pytest.raises(
            InvalidQuantityError, match="Insufficient available quantity"
        ):
            holding.reserve(Quantity(150))

    def test_reserve_zero_quantity(self):
        instrument_id = InstrumentId.generate()
        holding = Holding(
            instrument_id, Quantity(100), Quantity(50), Money("150.50", Currency.USD)
        )

        holding.reserve(Quantity(0))

        assert holding.available == Quantity(100)
        assert holding.reserved == Quantity(50)

    def test_release_valid(self):
        instrument_id = InstrumentId.generate()
        holding = Holding(
            instrument_id, Quantity(100), Quantity(50), Money("150.50", Currency.USD)
        )

        holding.release(Quantity(20))

        assert holding.available == Quantity(120)
        assert holding.reserved == Quantity(30)

    def test_release_insufficient_reserved(self):
        instrument_id = InstrumentId.generate()
        holding = Holding(
            instrument_id, Quantity(100), Quantity(50), Money("150.50", Currency.USD)
        )

        with pytest.raises(
            InvalidQuantityError, match="Insufficient reserved quantity"
        ):
            holding.release(Quantity(60))

    def test_release_exact_reserved(self):
        instrument_id = InstrumentId.generate()
        holding = Holding(
            instrument_id, Quantity(100), Quantity(50), Money("150.50", Currency.USD)
        )

        holding.release(Quantity(50))

        assert holding.available == Quantity(150)
        assert holding.reserved == Quantity(0)

    def test_consume_reserved_valid(self):
        instrument_id = InstrumentId.generate()
        holding = Holding(
            instrument_id, Quantity(100), Quantity(50), Money("150.50", Currency.USD)
        )

        holding.consume_reserved(Quantity(20))

        assert holding.available == Quantity(100)
        assert holding.reserved == Quantity(30)

    def test_consume_reserved_insufficient(self):
        instrument_id = InstrumentId.generate()
        holding = Holding(
            instrument_id, Quantity(100), Quantity(50), Money("150.50", Currency.USD)
        )

        with pytest.raises(
            InvalidQuantityError, match="Insufficient reserved quantity"
        ):
            holding.consume_reserved(Quantity(60))

    def test_consume_reserved_exact(self):
        instrument_id = InstrumentId.generate()
        holding = Holding(
            instrument_id, Quantity(100), Quantity(50), Money("150.50", Currency.USD)
        )

        holding.consume_reserved(Quantity(50))

        assert holding.available == Quantity(100)
        assert holding.reserved == Quantity(0)

    def test_update_average_cost_valid(self):
        instrument_id = InstrumentId.generate()
        holding = Holding(
            instrument_id, Quantity(100), Quantity(50), Money("150.50", Currency.USD)
        )

        new_average_cost = Money("155.75", Currency.USD)
        holding.update_average_cost(new_average_cost)

        assert holding.average_cost == new_average_cost

    def test_update_average_cost_same_currency(self):
        instrument_id = InstrumentId.generate()
        holding = Holding(
            instrument_id, Quantity(100), Quantity(50), Money("150.50", Currency.USD)
        )

        new_average_cost = Money("155.75", Currency.USD)
        holding.update_average_cost(new_average_cost)

        assert holding.average_cost.currency == Currency.USD

    def test_update_average_cost_different_currency(self):
        instrument_id = InstrumentId.generate()
        holding = Holding(
            instrument_id, Quantity(100), Quantity(50), Money("150.50", Currency.USD)
        )

        new_average_cost = Money("155.75", Currency.EUR)

        with pytest.raises(CurrencyMismatchError, match="Currency mismatch"):
            holding.update_average_cost(new_average_cost)

    def test_multiple_operations_sequence(self):
        instrument_id = InstrumentId.generate()
        holding = Holding(
            instrument_id, Quantity(100), Quantity(0), Money("150.50", Currency.USD)
        )

        # Add
        holding.add(Quantity(50))
        assert holding.available == Quantity(150)
        assert holding.reserved == Quantity(0)

        # Reserve
        holding.reserve(Quantity(30))
        assert holding.available == Quantity(120)
        assert holding.reserved == Quantity(30)

        # Release
        holding.release(Quantity(10))
        assert holding.available == Quantity(130)
        assert holding.reserved == Quantity(20)

        # Consume reserved
        holding.consume_reserved(Quantity(20))
        assert holding.available == Quantity(130)
        assert holding.reserved == Quantity(0)

        # Remove
        holding.remove(Quantity(50))
        assert holding.available == Quantity(80)
        assert holding.reserved == Quantity(0)
