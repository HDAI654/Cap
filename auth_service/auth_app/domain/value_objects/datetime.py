from datetime import datetime, timezone


class DateTime:
    def __init__(self, value: str = None):
        if value is None:
            self._value = datetime.now(timezone.utc)
        else:
            if not isinstance(value, str):
                raise TypeError(f"DateTime must be string, got {type(value).__name__}")
            value = value.strip()
            if not value:
                raise ValueError("DateTime must be a non-empty string")
            try:
                self._value = datetime.fromisoformat(value)
            except:
                raise ValueError("DateTime value must be yyyy-mm-dd")

    @property
    def value(self) -> str:
        return self._value.isoformat()

    def __str__(self):
        return self.value

    def __repr__(self):
        return f"DateTime('{self.value}')"

    def __eq__(self, other):
        if isinstance(other, DateTime):
            return self.value == other.value
        if isinstance(other, str):
            return self.value == other.strip()
        return False

    def __hash__(self):
        return hash((self.value,))
