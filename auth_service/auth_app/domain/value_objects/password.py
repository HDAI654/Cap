class Password:
    def __init__(self, hashed_value: str):
        self._hashed = hashed_value

    @property
    def value(self):
        return self._hashed

    def __eq__(self, other):
        return isinstance(other, Password) and self.value == other.value
