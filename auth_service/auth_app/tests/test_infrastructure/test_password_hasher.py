import pytest
from auth_app.infrastructure.security.password_hasher import PasswordHasher


class TestsPasswordHasher:
    hasher = PasswordHasher()

    def test_hash_returns_different_value_than_plain(self):
        password = "StrongPassword123!"
        hashed = self.hasher.hash(password)

        assert hashed != password
        assert isinstance(hashed, str)

    def test_verify_correct_password_returns_true(self):
        password = "StrongPassword123!"
        hashed = self.hasher.hash(password)

        assert self.hasher.verify(password, hashed) is True

    def test_verify_wrong_password_returns_false(self):
        password = "StrongPassword123!"
        hashed = self.hasher.hash(password)

        assert self.hasher.verify("WrongPassword!", hashed) is False

    def test_hash_same_password_generates_different_hashes(self):
        password = "StrongPassword123!"
        hash1 = self.hasher.hash(password)
        hash2 = self.hasher.hash(password)

        assert hash1 != hash2
