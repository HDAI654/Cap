from core.crypto_utils import IDGenerator


class ID:
    def __init__(self, value: str = None):
        if value is None:
            value = IDGenerator.generate()
        if not isinstance(value, str) or not value.strip():
            raise ValueError("ID value must be a non-empty string")
        self._value = value.strip()

    @property
    def value(self) -> str:
        return self._value

    def __str__(self):
        return self.value

    def __repr__(self):
        return f"ID('{self.value}')"

    def __eq__(self, other):
        if isinstance(other, ID):
            return self.value == other.value
        if isinstance(other, str):
            return self.value == other.strip().lower()
        return False

    def __hash__(self):
        return hash(self.value)
