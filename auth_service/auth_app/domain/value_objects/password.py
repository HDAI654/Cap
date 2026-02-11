class Password:
    def __init__(self, hashed_value: str):
        if not isinstance(hashed_value, str):
            raise TypeError(f"Password must be string, got {type(hashed_value).__name__}")
        hashed_value = hashed_value.strip()
        if not hashed_value:
            raise ValueError("Password must be a non-empty string")
        self._hashed = hashed_value

    @property
    def value(self):
        return self._hashed

    def __eq__(self, other):
        return isinstance(other, Password) and self.value == other.value
