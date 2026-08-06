from src.domain.entities.user import User
from src.domain.value_objects.hashed_password import HashedPassword
from src.domain.value_objects.role import Role


def test_create_defaults_to_user_role() -> None:
    user = User.create(email="a@b.com", hashed_password="hash")
    assert user.role == Role.user()
    assert user.email.value == "a@b.com"
    assert user.hashed_password.value == "hash"


def test_create_with_explicit_role() -> None:
    user = User.create(email="a@b.com", hashed_password="hash", role="ADMIN")
    assert user.role == Role.admin()


def test_change_password() -> None:
    user = User.create(email="a@b.com", hashed_password="old")
    user.change_password(HashedPassword("new-hash"))
    assert user.hashed_password.value == "new-hash"


def test_equality_by_state() -> None:
    u1 = User.create(email="a@b.com", hashed_password="h", id="11111111-1111-4111-8111-111111111111")
    u2 = User.create(email="a@b.com", hashed_password="h", id="11111111-1111-4111-8111-111111111111")
    assert u1 == u2
