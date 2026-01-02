import pytest
from auth_app.domain.value_objects.email import Email


class TestEmail:
    def test_not_str_email(self):
        with pytest.raises(ValueError):
            Email(25)
            Email(None)

    def test_empty_str_email(self):
        with pytest.raises(ValueError):
            Email("")

    def test_invalid_email(self):
        with pytest.raises(ValueError):
            Email("ssss12111._com@@sjk")

    def test_email_strip(self):
        str_email = "        testemail@test.com  "
        email = Email(str_email)

        assert email.value == str_email.strip()

    def test_eq_email(self):
        email = Email("testemail@test.com")
        email2 = Email("testemail@test.com")

        assert email == email2
        assert email == "testemail@test.com" and email2 == "testemail@test.com"
