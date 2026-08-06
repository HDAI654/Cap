import pytest
from src.domain.value_objects.role import Role
from src.exceptions import InvalidRoleError


def test_user_factory() -> None:
    assert Role.user().value == "USER"
    assert Role.user().is_admin is False


def test_admin_factory() -> None:
    assert Role.admin().value == "ADMIN"
    assert Role.admin().is_admin is True


def test_normalizes_case() -> None:
    assert Role("admin").value == "ADMIN"


def test_rejects_unknown() -> None:
    with pytest.raises(InvalidRoleError):
        Role("GUEST")
