from datetime import datetime, timezone


class DateTime:
    def __init__(self, value: str = None):
        if value is None:
            self._value = datetime.now(timezone.utc)
        elif not isinstance(value, str) or not value.strip():
            raise ValueError("DateTime value must be a non-empty string")
        else:
            try:
                self._value = datetime.fromisoformat(value.strip())
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
        return hash(self.value)
