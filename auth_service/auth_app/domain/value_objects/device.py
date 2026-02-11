class Device:
    def __init__(self, value: str):
        if not isinstance(value, str):
            raise TypeError(f"Device must be string, got {type(value).__name__}")
        value = value.strip()
        if not value:
            raise ValueError("Device must be a non-empty string")

        self._value = value

    @property
    def value(self) -> str:
        return self._value

    def __str__(self):
        return self.value

    def __repr__(self):
        return f"Device('{self.value}')"

    def __eq__(self, other):
        if isinstance(other, Device):
            return self.value == other.value
        if isinstance(other, str):
            return self.value == other.strip()
        return False

    def __hash__(self):
        return hash((self.value,))
