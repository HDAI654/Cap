import pytest

from auth_app.domain.user import UserEntity, UserValidator


class TestUserValidator:
    def test_validate_username_raises_on_empty_string(self):
        with pytest.raises(ValueError, match="username can't be empty"):
            UserValidator.validate_username("")

    def test_validate_username_raises_on_whitespace_only(self):
        with pytest.raises(ValueError, match="username can't be empty"):
            UserValidator.validate_username("   ")

    def test_validate_username_returns_stripped_username(self):
        assert UserValidator.validate_username("  testuser  ") == "testuser"

    def test_validate_username_raises_on_invalid_characters(self):
        invalid_usernames = ["ab", "a" * 31, "user@name", "user-name"]
        for username in invalid_usernames:
            with pytest.raises(ValueError, match="Username must be 3–30 chars"):
                UserValidator.validate_username(username)

    def test_validate_username_accepts_valid_usernames(self):
        valid_usernames = ["user", "user123", "user.name", "user_name", "u" * 30]
        for username in valid_usernames:
            assert UserValidator.validate_username(username) == username

    def test_validate_email_returns_none_for_empty(self):
        assert UserValidator.validate_email("") is None
        assert UserValidator.validate_email("   ") is None

    def test_validate_email_returns_stripped_email(self):
        assert (
            UserValidator.validate_email("  user@example.com  ") == "user@example.com"
        )

    def test_validate_email_raises_on_invalid_format(self):
        invalid_emails = ["user", "user@", "@example.com", "user@.com"]
        for email in invalid_emails:
            with pytest.raises(ValueError, match="Invalid email"):
                UserValidator.validate_email(email)

    def test_validate_email_accepts_valid_emails(self):
        valid_emails = [
            "user@example.com",
            "user.name@example.co.uk",
            "user+tag@example.org",
        ]
        for email in valid_emails:
            assert UserValidator.validate_email(email) == email

    def test_validate_password_raises_on_empty(self):
        with pytest.raises(ValueError, match="password can't be empty"):
            UserValidator.validate_password("")

    def test_validate_password_raises_on_whitespace_only(self):
        with pytest.raises(ValueError, match="password can't be empty"):
            UserValidator.validate_password("   ")

    def test_validate_password_raises_on_contains_spaces(self):
        with pytest.raises(ValueError, match="Password must not contain spaces"):
            UserValidator.validate_password("pass word")

    def test_validate_password_raises_on_too_short(self):
        with pytest.raises(ValueError, match="Password must be at least 8 characters"):
            UserValidator.validate_password("short")

    def test_validate_password_returns_stripped_password(self):
        assert UserValidator.validate_password("  password123  ") == "password123"

    def test_validate_password_accepts_valid_passwords(self):
        valid_passwords = ["password", "p" * 8, "verylongpassword123", "pass_word123"]
        for password in valid_passwords:
            assert UserValidator.validate_password(password) == password


class TestUserEntity:
    def test_entity_creation_with_valid_data(self):
        user = UserEntity(
            username="testuser", email="test@example.com", password="password123"
        )

        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.password == "password123"
        assert user.id is None

    def test_entity_creation_with_id(self):
        user = UserEntity(
            id=1, username="testuser", email="test@example.com", password="password123"
        )

        assert user.id == 1

    def test_entity_creation_strips_inputs(self):
        user = UserEntity(
            username="  testuser  ",
            email="  test@example.com  ",
            password="  password123  ",
        )

        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.password == "password123"

    def test_entity_creation_validates_username(self):
        with pytest.raises(ValueError, match="username can't be empty"):
            UserEntity(username="", email="test@example.com", password="password123")

    def test_entity_creation_validates_email(self):
        with pytest.raises(ValueError, match="Invalid email"):
            UserEntity(username="testuser", email="invalid", password="password123")

    def test_entity_creation_allows_none_email(self):
        user = UserEntity(username="testuser", email="", password="password123")

        assert user.email is None

    def test_entity_creation_validates_password(self):
        with pytest.raises(ValueError, match="password can't be empty"):
            UserEntity(username="testuser", email="test@example.com", password="")

    def test_entity_equality_based_on_id(self):
        user1 = UserEntity(id=1, username="user1", email="a@test.com", password="password")
        user2 = UserEntity(id=1, username="user2", email="b@test.com", password="pass2word")
        user3 = UserEntity(id=2, username="user1", email="a@test.com", password="password")

        assert user1 == user1
        assert user1 == user2
        assert user1 != user3
        assert user1 is not user2

    def test_entity_hash_based_on_id(self):
        user1 = UserEntity(id=1, username="user1", email="a@test.com", password="password")
        user2 = UserEntity(id=1, username="user2", email="b@test.com", password="pass2word")

        assert hash(user1) == hash(user2)

    def test_entity_with_none_id_equality(self):
        user1 = UserEntity(
            id=None, username="user", email="a@test.com", password="password"
        )
        user2 = UserEntity(
            id=None, username="user", email="a@test.com", password="password"
        )

        assert user1 != user2

    def test_from_model_creates_entity(self):
        class MockModel:
            id = 1
            username = "testuser"
            email = "test@example.com"
            password = "hashedpassword"

        mock_model = MockModel()
        user = UserEntity.from_model(mock_model)

        assert user.id == 1
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.password == "hashedpassword"
