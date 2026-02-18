from django.contrib.auth.hashers import make_password, check_password
from core.exceptions import PasswordHasherError


class PasswordHasher:
    def hash(self, password: str) -> str:
        if not isinstance(password, str):
            raise TypeError(
                f"PasswordHasher.verify() argument 'password' must be string, got {type(password).__name__}"
            )
        try:
            return make_password(password)
        except Exception as e:
            raise PasswordHasherError(
                f"Unexpected error occurred during hashing password:\n{str(e)}"
            ) from e

    def verify(self, plain: str, hashed: str) -> bool:
        if not isinstance(plain, str):
            raise TypeError(
                f"PasswordHasher.verify() argument 'plain' must be string, got {type(plain).__name__}"
            )
        if not isinstance(hashed, str):
            raise TypeError(
                f"PasswordHasher.verify() argument 'hashed' must be string, got {type(hashed).__name__}"
            )
        try:
            return check_password(plain, hashed)
        except Exception as e:
            raise PasswordHasherError(
                f"Unexpected error occurred during verifying password:\n{str(e)}"
            ) from e
