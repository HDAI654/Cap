import pytest
from auth_app.domain.value_objects.email import Email


class TestEmail:
    def test_not_str_email(self):
        with pytest.raises(TypeError):
            Email(25)
            Email(None)

    def test_empty_str_email(self):
        with pytest.raises(ValueError):
            Email("")
            Email(" ")
            Email("    ")

    def test_invalid_email(self):
        with pytest.raises(ValueError):
            Email("ssss12111._com@@sjk")
            Email("A"*65+"@gmail.com")
            Email("Aaaaaaa@"+"g"*256+".com")
            Email("A"*235+"@gmail.com")
            Email("A@dweuu@gmail.com")

    def test_blocked_emails(self):
        with pytest.raises(ValueError):
            Email("MyEmail@10minutemail.com")
            Email("yopmail.com")
            Email("trashmail.com")
            Email("throwawaymail.com")

    def test_email_strip(self):
        str_email = "        testemail@test.com  "
        email = Email(str_email)

        assert email.value == str_email.strip()

    def test_email_lower(self):
        email1 = Email("MyEmail@gmail.com")
        email2 = Email("MYEMAIL@gmail.com")

        assert email1.value == email2.value

    def test_eq_email(self):
        email = Email("testemail@test.com")
        email2 = Email("testemail@test.com")

        assert email == email2
        assert email == "testemail@test.com" and email2 == "testemail@test.com"
