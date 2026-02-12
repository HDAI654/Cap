import pytest
from auth_app.domain.value_objects.password import Password


class TestPassword:
    def test_not_str_password(self):
        with pytest.raises(TypeError):
            Password(25)
            Password(None)

    def test_empty_str_password(self):
        with pytest.raises(ValueError):
            Password("")
            Password(" ")
            Password("  ")
    
    def test_email_strip(self):
        psw = Password("      TheHashedValueOfPassword    ")

        assert psw.value == "TheHashedValueOfPassword"

    def test_eq_password(self):
        password = Password("MyPassword")
        password2 = Password("MyPassword")

        assert password == password2
