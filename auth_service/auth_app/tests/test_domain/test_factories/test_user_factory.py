from auth_app.domain.factories.user_factory import UserFactory


class TestUserFactory:
    def test_create_success(self):
        user = UserFactory.create(
            user_id="MyID",
            username="TestUsername123",
            email="testmail@test.com",
            hashed_password="MyHashedPassword",
        )

        assert user.id.value == "MyID"
        assert user.username.value == "TestUsername123"
        assert user.email.value == "testmail@test.com"
        assert user.password.value == "MyHashedPassword"

    def test_create_success_with_none_id(self):
        user = UserFactory.create(
            username="TestUsername123",
            email="testmail@test.com",
            hashed_password="MyHashedPassword",
        )

        assert user.id.value
        assert user.username.value == "TestUsername123"
        assert user.email.value == "testmail@test.com"
        assert user.password.value == "MyHashedPassword"
