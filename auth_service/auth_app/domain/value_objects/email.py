import re

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

BLOCKLIST = {
    "mailinator.com",
    "temp-mail.org",
    "guerrillamail.com",
    "10minutemail.com",
    "yopmail.com",
    "trashmail.com",
    "throwawaymail.com",
    "emailondeck.com",
    "mail.tm",
    "tempmail.net",
}

class Email:
    def __init__(self, value: str):
        if not isinstance(value, str):
            raise TypeError(f"Email must be string, got {type(value).__name__}")
        value = value.strip().lower()
        if not value:
            raise ValueError("Email must be a non-empty string")
        if not EMAIL_REGEX.match(value) or len(value) > 254 or value.split("@")[1] in BLOCKLIST:
            raise ValueError("Invalid Email !")

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
        return hash((self.value,))
