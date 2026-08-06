from datetime import date
from src.domain.entities.session import Session
from src.domain.entities.user import User


def test_create_binds_user_and_device() -> None:
    user = User.create(email="a@b.com", hashed_password="h")
    session = Session.create(user_id=user.id.value, device="web")
    assert session.user_id == user.id
    assert session.device.value == "web"
    assert session.created_at.value == date.today()


def test_create_with_explicit_id_and_date() -> None:
    sid = "22222222-2222-4222-8222-222222222222"
    uid = "11111111-1111-4111-8111-111111111111"
    session = Session.create(
        user_id=uid, device="ios", id=sid, created_at="2026-01-15"
    )
    assert session.id.value == sid
    assert session.created_at.value == date(2026, 1, 15)
