import pytest
from src.domain.value_objects.quantity import Quantity
from src.exceptions import InvalidQuantityError, QuantityOperationError


class TestQuantity:
    def test_valid_quantity_creation(self):
        quantity = Quantity(10)
        assert quantity.value == 10

    def test_quantity_zero(self):
        quantity = Quantity(0)
        assert quantity.value == 0

    def test_quantity_negative(self):
        with pytest.raises(InvalidQuantityError):
            Quantity(-1)

    def test_quantity_non_integer(self):
        with pytest.raises(InvalidQuantityError):
            Quantity(10.5)

        with pytest.raises(InvalidQuantityError):
            Quantity("10")

    def test_quantity_addition(self):
        q1 = Quantity(10)
        q2 = Quantity(5)
        result = q1 + q2

        assert result.value == 15

    def test_quantity_addition_invalid_operand(self):
        q = Quantity(10)

        with pytest.raises(QuantityOperationError):
            q + 5

    def test_quantity_subtraction(self):
        q1 = Quantity(10)
        q2 = Quantity(5)
        result = q1 - q2

        assert result.value == 5

    def test_quantity_subtraction_negative_result(self):
        q1 = Quantity(5)
        q2 = Quantity(10)

        with pytest.raises(InvalidQuantityError):
            q1 - q2

    def test_quantity_subtraction_invalid_operand(self):
        q = Quantity(10)

        with pytest.raises(QuantityOperationError):
            q - 5

    def test_quantity_less_than(self):
        q1 = Quantity(10)
        q2 = Quantity(15)

        assert q1 < q2
        assert not (q2 < q1)

    def test_quantity_less_than_invalid_operand(self):
        q = Quantity(10)

        with pytest.raises(QuantityOperationError):
            q < 5

    def test_quantity_less_than_or_equal(self):
        q1 = Quantity(10)
        q2 = Quantity(10)
        q3 = Quantity(15)

        assert q1 <= q2
        assert q1 <= q3
        assert not (q3 <= q1)

    def test_quantity_greater_than(self):
        q1 = Quantity(15)
        q2 = Quantity(10)

        assert q1 > q2
        assert not (q2 > q1)

    def test_quantity_greater_than_or_equal(self):
        q1 = Quantity(10)
        q2 = Quantity(10)
        q3 = Quantity(15)

        assert q1 >= q2
        assert q3 >= q1
        assert not (q1 >= q3)

    def test_quantity_equality(self):
        q1 = Quantity(10)
        q2 = Quantity(10)
        q3 = Quantity(15)

        assert q1 == q2
        assert q1 != q3

    def test_quantity_hash(self):
        q1 = Quantity(10)
        q2 = Quantity(10)

        assert hash(q1) == hash(q2)

    def test_quantity_str_representation(self):
        q = Quantity(10)
        assert str(q) == "10"
