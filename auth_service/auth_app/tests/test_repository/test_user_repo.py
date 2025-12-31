import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist

from auth_app.repository.user_repository import UserRepo
from core.exceptions import UserAlreadyExists, AuthenticationFailed
from auth_service.auth_app.domain.entities.user import UserEntity

User = get_user_model()


@pytest.mark.django_db
class TestUserRepository:
    def test_create_user_success(self):
        user_entity = UserEntity(
            username="testuser", email="test@example.com", password="validpassword123"
        )

        result = UserRepo.create_user(user_entity)

        # Verify database state
        assert User.objects.filter(id=result.id).exists()
        db_user = User.objects.get(id=result.id)
        assert db_user.username == "testuser"
        assert db_user.email == "test@example.com"
        assert db_user.check_password("validpassword123")

        # Verify returned entity
        assert result.id == db_user.id
        assert result.username == "testuser"
        assert result.email == "test@example.com"
        assert isinstance(result, UserEntity)

    def test_create_user_requires_email(self):
        user_entity = UserEntity(username="noemail", email="", password="password123")

        with pytest.raises(ValueError, match="email is required"):
            UserRepo.create_user(user_entity)

        assert User.objects.filter(username="noemail").count() == 0

    def test_create_user_duplicate_username(self):
        # Create first user
        UserRepo.create_user(
            UserEntity(
                username="duplicate", email="first@example.com", password="pass1234"
            )
        )

        # Attempt duplicate username
        with pytest.raises(
            UserAlreadyExists, match="Username 'duplicate' is already taken"
        ):
            UserRepo.create_user(
                UserEntity(
                    username="duplicate",
                    email="second@example.com",
                    password="pass1234",
                )
            )

        # Verify only one user exists
        assert User.objects.filter(username="duplicate").count() == 1

    def test_create_user_duplicate_email(self):
        # Create first user
        UserRepo.create_user(
            UserEntity(username="user1", email="same@example.com", password="pass1234")
        )

        # Attempt duplicate email
        with pytest.raises(
            UserAlreadyExists, match="Email 'same@example.com' is already registered"
        ):
            UserRepo.create_user(
                UserEntity(
                    username="user2", email="same@example.com", password="pass1234"
                )
            )

        # Verify only one user with that email
        assert User.objects.filter(email="same@example.com").count() == 1

    def test_create_user_case_insensitive_email_uniqueness(self):
        UserRepo.create_user(
            UserEntity(username="user1", email="TEST@example.com", password="pass1234")
        )

        # Different case should still trigger duplicate
        with pytest.raises(
            UserAlreadyExists, match="Email 'test@example.com' is already registered"
        ):
            UserRepo.create_user(
                UserEntity(
                    username="user2", email="test@example.com", password="pass1234"
                )
            )

    def test_create_user_case_insensitive_username_uniqueness(self):
        UserRepo.create_user(
            UserEntity(
                username="TestUser", email="user1@example.com", password="pass1234"
            )
        )

        # Different case should still trigger duplicate
        with pytest.raises(
            UserAlreadyExists, match="Username 'testuser' is already taken"
        ):
            UserRepo.create_user(
                UserEntity(
                    username="testuser", email="user2@example.com", password="pass1234"
                )
            )

    def test_authenticate_success(self):
        # Create user directly to ensure password is set
        user = User.objects.create_user(
            username="authuser", email="auth@example.com", password="correctpassword"
        )

        user_entity = UserEntity(
            id=user.id,
            username="authuser",
            email="auth@example.com",
            password="correctpassword",
        )

        result = UserRepo.authenticate(user_entity)

        assert result.id == user.id
        assert result.username == user.username
        assert result.email == user.email
        assert isinstance(result, UserEntity)

    def test_authenticate_wrong_password(self):
        User.objects.create_user(
            username="testuser", email="test@example.com", password="rightpassword"
        )

        user_entity = UserEntity(
            username="testuser", email="", password="wrongpassword"
        )

        with pytest.raises(AuthenticationFailed, match="Invalid username or password"):
            UserRepo.authenticate(user_entity)

    def test_authenticate_nonexistent_username(self):
        user_entity = UserEntity(
            username="nonexistent", email="", password="anypassword"
        )

        with pytest.raises(AuthenticationFailed, match="Invalid username or password"):
            UserRepo.authenticate(user_entity)

    def test_get_by_id_found(self):
        user = User.objects.create_user(
            username="getuser", email="get@example.com", password="password123"
        )

        result = UserRepo.get_by_id(str(user.id))

        assert result.id == user.id
        assert result.username == user.username
        assert result.email == user.email
        assert isinstance(result, UserEntity)

    def test_get_by_id_not_found(self):
        # Create a user to ensure IDs exist
        existing_user = User.objects.create_user(
            username="existing", email="existing@example.com", password="pass"
        )

        non_existent_id = existing_user.id + 1000

        with pytest.raises(ObjectDoesNotExist):
            result = UserRepo.get_by_id(str(non_existent_id))

            assert hasattr(result, "id")
            assert hasattr(result, "username")
            assert hasattr(result, "email")
            assert hasattr(result, "password")

    def test_get_by_id_invalid_id_format(self):
        with pytest.raises(ValueError):
            UserRepo.get_by_id("not-a-number")

    def test_concurrent_user_creation_race_condition(self):
        # This tests database-level constraint, not application logic
        user_entity = UserEntity(
            username="raceuser", email="race@example.com", password="password123"
        )

        # Simulate race by creating user directly in DB first
        User.objects.create_user(
            username="raceuser", email="race@example.com", password="otherpassword"
        )

        # Repository should catch the duplicate
        with pytest.raises(UserAlreadyExists):
            UserRepo.create_user(user_entity)

    def test_authenticate_with_inactive_user(self):
        user = User.objects.create_user(
            username="inactive", email="inactive@example.com", password="password123"
        )
        user.is_active = False
        user.save()

        user_entity = UserEntity(username="inactive", email="", password="password123")

        # Django's authenticate() returns None for inactive users
        with pytest.raises(AuthenticationFailed):
            UserRepo.authenticate(user_entity)

    def test_password_hashing_on_create(self):
        user_entity = UserEntity(
            username="hashuser", email="hash@example.com", password="plaintextpassword"
        )

        result = UserRepo.create_user(user_entity)

        db_user = User.objects.get(id=result.id)
        # Password should be hashed, not stored plaintext
        assert db_user.password != "plaintextpassword"
        assert db_user.check_password("plaintextpassword")
        assert not db_user.check_password("wrongpassword")
