import re

EMAIL_REGEX = re.compile(
    r"^[A-Za-z0-9._%+-]{1,64}@" r"[A-Za-z0-9.-]{1,255}\.[A-Za-z]{2,}$"
)


class Email:
    def __init__(self, value: str):
        if not isinstance(value, str):
            raise ValueError("Email value must be a non-empty string")
        value = value.strip().lower()
        if not value:
            raise ValueError("Device value must be a non-empty string")
        if not EMAIL_REGEX.match(value) or len(value) > 254:
            raise ValueError("Invalid email !")

        self._value = value

    @property
    def value(self) -> str:
        return self._value

    def __str__(self):
        return self.value

    def __repr__(self):
        return f"Email('{self.value}')"

    def __eq__(self, other):
        if isinstance(other, Email):
            return self.value == other.value
        if isinstance(other, str):
            return self.value == other.strip().lower()
        return False

    def __hash__(self):
        return hash(self.value)
