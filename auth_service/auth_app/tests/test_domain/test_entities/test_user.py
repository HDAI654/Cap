from auth_app.domain.entities.user import UserEntity
from auth_app.domain.value_objects.id import ID
from auth_app.domain.value_objects.username import Username
from auth_app.domain.value_objects.email import Email
from auth_app.domain.value_objects.password import Password


class TestUser:
    def test_none_id(self):
        user = UserEntity(
            username=Username("MyUsername123"),
            email=Email("testmail@test.com"),
            password=Password("hashed password"),
        )

        assert user.id.value != None

    def test_eq_id(self):
        user = UserEntity(
            id=ID("MyID"),
            username=Username("MyUsername123"),
            email=Email("testmail@test.com"),
            password=Password("hashed password"),
        )
        user2 = UserEntity(
            id=ID("MyID"),
            username=Username("MyUsername123"),
            email=Email("testmail@test.com"),
            password=Password("hashed password"),
        )
        user3 = UserEntity(
            username=Username("MyUsername123"),
            email=Email("testmail@test.com"),
            password=Password("hashed password"),
        )

        assert user == user2
        assert user != user3 and user2 != user3
