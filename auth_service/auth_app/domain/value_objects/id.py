from core.crypto_utils import IDGenerator

class ID:
    def __init__(self, value: str = None):
        if value is None:
            self._value = IDGenerator.generate()
        else:
            if not isinstance(value, str):
                raise TypeError(f"ID must be string, got {type(value).__name__}")
            value = value.strip()
            if not value:
                raise ValueError("ID must be a non-empty string")
            if not value.isascii():
                raise ValueError("ID must contain only ASCII characters")
            
            self._value = value
        
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
            return self.value == other.strip()
        return False

    def __hash__(self):
        return hash((self.value,))
