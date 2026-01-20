import pytest
from auth_app.domain.value_objects.password import Password


class TestPassword:
    def test_eq_password(self):
        password = Password("MyPassword")
        password2 = Password("MyPassword")

        assert password == password2
