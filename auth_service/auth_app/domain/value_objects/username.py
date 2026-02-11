class Username:
    def __init__(self, value: str):
        if not isinstance(value, str):
            raise TypeError(f"Username must be string, got {type(value).__name__}")
        value = value.strip()
        if not value:
            raise ValueError("Username must be a non-empty string")
        if not value.isascii():
            raise ValueError("Username must contain only ASCII characters")

        self._value = value

    @property
    def value(self) -> str:
        return self._value

    def __str__(self):
        return self.value

    def __repr__(self):
        return f"Username('{self.value}')"

    def __eq__(self, other):
        if isinstance(other, Username):
            return self.value == other.value
        if isinstance(other, str):
            return self.value == other.strip()
        return False

    def __hash__(self):
        return hash((self.value,))
