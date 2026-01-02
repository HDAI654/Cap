from django.contrib.auth.hashers import make_password, check_password


class PasswordHasher:
    def hash(self, password: str) -> str:
        return make_password(password)

    def verify(self, plain: str, hashed: str) -> bool:
        return check_password(plain, hashed)
