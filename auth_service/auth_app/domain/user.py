import re

USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9_.]{3,30}$")
EMAIL_REGEX = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


class UserValidator:
    @staticmethod
    def validate_username(username: str):
        username = username.strip()
        if not username:
            raise ValueError("username can't be empty")
        if not USERNAME_REGEX.match(username):
            raise ValueError("Username must be 3–30 chars: letters, numbers, _ or .")
        return username

    @staticmethod
    def validate_email(email: str):
        email = email.strip()
        if not email:
            return None
        if not EMAIL_REGEX.match(email):
            raise ValueError("Invalid email")
        return email

    @staticmethod
    def validate_password(password: str):
        password = password.strip()
        if not password:
            raise ValueError("password can't be empty")
        if " " in password:
            raise ValueError("Password must not contain spaces")
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return password


class UserEntity:
    def __init__(self, username: str, email: str, password: str, id: int | None = None):
        self.id = id
        self.username = UserValidator.validate_username(username)
        self.email = UserValidator.validate_email(email)
        self.password = UserValidator.validate_password(password)

    @classmethod
    def from_model(cls, user_model):
        return cls(
            id=user_model.id,
            username=user_model.username,
            email=user_model.email,
            password=user_model.password,
        )
