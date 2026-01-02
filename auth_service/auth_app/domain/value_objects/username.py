import re

USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9_.]{3,30}$")


class Username:
    def __init__(self, value: str):
        if not isinstance(value, str):
            raise ValueError("Username value must be a non-empty string")
        value = value.strip()
        if not value:
            raise ValueError("Username value can't be empty")
        if not USERNAME_REGEX.match(value):
            raise ValueError(
                "Username value must be 3–30 chars: letters, numbers, _ or ."
            )

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
        return hash(self.value)
