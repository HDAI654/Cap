import pytest
from src.domain.value_objects.email_verification_token import EmailVerificationToken
from src.exceptions import InvalidEmailVerificationTokenError


def test_generate_roundtrip() -> None:
    tok = EmailVerificationToken.generate()
    assert EmailVerificationToken(tok.value) == tok


def test_rejects_invalid() -> None:
    with pytest.raises(InvalidEmailVerificationTokenError):
        EmailVerificationToken("not-uuid")
