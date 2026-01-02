import pytest
from auth_app.domain.value_objects.username import Username


class TestUsername:
    def test_not_str_username(self):
        with pytest.raises(ValueError):
            Username(25)
            Username(None)

    def test_empty_str_username(self):
        with pytest.raises(ValueError):
            Username("")

    def test_invalid_username(self):
        with pytest.raises(ValueError):
            Username("نام کاربری")

    def test_username_strip(self):
        str_username = "        username  "
        username = Username(str_username)

        assert username.value == str_username.strip()

    def test_eq_username(self):
        username = Username("MyUsername")
        username2 = Username("MyUsername")

        assert username == username2
        assert username == "MyUsername" and username2 == "MyUsername"
