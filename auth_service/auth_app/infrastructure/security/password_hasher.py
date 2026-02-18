from django.contrib.auth.hashers import make_password, check_password
from core.exceptions import PasswordHasherError


class PasswordHasher:
    def hash(self, password: str) -> str:
        try:
            return make_password(password)
        except Exception as e:
            raise PasswordHasherError(
                f"Unexpected error occurred during hashing password:\n{str(e)}"
            ) from e

    def verify(self, plain: str, hashed: str) -> bool:
        try:
            return check_password(plain, hashed)
        except Exception as e:
            raise PasswordHasherError(
                f"Unexpected error occurred during verifying password:\n{str(e)}"
            ) from e
