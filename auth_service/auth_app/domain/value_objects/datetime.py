from datetime import datetime, timezone


class DateTime:
    def __init__(self, value: float | int = None):
        if value is None:
            self._value = datetime.now(timezone.utc)
        else:
            value = float(value) if isinstance(value, int) else value
            if not isinstance(value, float):
                raise TypeError(f"DateTime must be float or integer, got {type(value).__name__}")
            if value <= 0:
                raise ValueError("DateTime must be positive")
            try:
                self._value = datetime.fromtimestamp(value, timezone.utc)
            except:
                raise ValueError("DateTime got invalid value")
    
    @property
    def value(self) -> float:
        return self._value.timestamp()

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return f"DateTime('{self.value}')"

    def __eq__(self, other):
        if isinstance(other, DateTime):
            return self.value == other.value
        if isinstance(other, (int, float)):
            return self.value == other
        return False

    def __hash__(self):
        return hash((self.value,))
