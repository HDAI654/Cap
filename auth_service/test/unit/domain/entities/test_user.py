from src.domain.entities.user import User
from src.domain.value_objects.hashed_password import HashedPassword
from src.domain.value_objects.role import Role
from src.domain.value_objects.user_id import UserId


def test_factory_generates_id_when_omitted() -> None:
    user = User.create(email="x@y.com", hashed_password="h")
    assert isinstance(user.id, UserId)
    assert len(user.id.value) == 36


def test_factory_uses_provided_id() -> None:
    uid = "33333333-3333-4333-8333-333333333333"
    user = User.create(email="x@y.com", hashed_password="h", id=uid)
    assert user.id.value == uid


def test_factory_defaults_role_to_user() -> None:
    user = User.create(email="x@y.com", hashed_password="h")
    assert user.role == Role.user()


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
    u1 = User.create(
        email="a@b.com", hashed_password="h", id="11111111-1111-4111-8111-111111111111"
    )
    u2 = User.create(
        email="a@b.com", hashed_password="h", id="11111111-1111-4111-8111-111111111111"
    )
    assert u1 == u2


def test_factory_generates_id_when_omitted() -> None:
    user = User.create(email="x@y.com", hashed_password="h")
    assert isinstance(user.id, UserId)
    assert len(user.id.value) == 36


def test_factory_uses_provided_id() -> None:
    uid = "33333333-3333-4333-8333-333333333333"
    user = User.create(email="x@y.com", hashed_password="h", id=uid)
    assert user.id.value == uid


def test_factory_defaults_role_to_user() -> None:
    user = User.create(email="x@y.com", hashed_password="h")
    assert user.role == Role.user()
