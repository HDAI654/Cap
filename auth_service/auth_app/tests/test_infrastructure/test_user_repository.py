import pytest
from auth_app.domain.factories.user_factory import UserFactory
from auth_app.infrastructure.persistence.repositories.user_repository import (
    DjangoUserRepository,
)
from auth_app.domain.entities.user import UserEntity

from auth_app.domain.value_objects.id import ID
from auth_app.domain.value_objects.email import Email
from auth_app.domain.value_objects.username import Username
from auth_app.domain.value_objects.password import Password

from django.contrib.auth import get_user_model
from core.exceptions import UserAlreadyExists, UserNotFound

User = get_user_model()


@pytest.mark.django_db
class TestUserRepo:
    repo = DjangoUserRepository()

    @pytest.fixture
    def valid_user_entity(self) -> UserEntity:
        return UserFactory.create(
            username="TestUser",
            email="testmail@test.com",
            hashed_password="TestPassword123",
        )

    def get_user_entity(self, username, email, hashed_password):
        return UserFactory.create(
            username=username, email=email, hashed_password=hashed_password
        )

    def test_add_success(self, valid_user_entity):
        result = self.repo.add(valid_user_entity)

        assert User.objects.filter(public_id=result.id.value).exists()
        db_user = User.objects.get(public_id=result.id.value)

        assert isinstance(result, UserEntity)
        assert result.username == db_user.username
        assert result.email == db_user.email
        assert result.password.value == db_user.password

    def test_add_duplicate_email(self, valid_user_entity):
        self.repo.add(valid_user_entity)

        with pytest.raises(UserAlreadyExists):
            self.repo.add(
                self.get_user_entity(
                    "DifferentUsername", valid_user_entity.email.value, "Password12345"
                )
            )

        assert User.objects.filter(username=valid_user_entity.username).count() == 1

    def test_add_duplicate_username(self, valid_user_entity):
        self.repo.add(valid_user_entity)

        with pytest.raises(UserAlreadyExists):
            self.repo.add(
                self.get_user_entity(
                    valid_user_entity.username.value,
                    "DifferentEmail@gmail.com",
                    "Password12345",
                )
            )

        assert User.objects.filter(username=valid_user_entity.username).count() == 1

    def test_save_success(self, valid_user_entity):
        self.repo.add(valid_user_entity)

        valid_user_entity.username = Username("new_username")
        valid_user_entity.email = Email("newtestmail@test.com")
        valid_user_entity.password = Password("NewTestPassword")

        self.repo.save(valid_user_entity)

        user = self.repo.get_by_id(id=valid_user_entity.id)

        assert user.id == valid_user_entity.id
        assert user.username == "new_username"
        assert user.email == "newtestmail@test.com"
        assert user.password.value == "NewTestPassword"

    def test_save_duplicate_email(self, valid_user_entity):
        self.repo.add(valid_user_entity)

        new_user = self.get_user_entity(
            username="DifferentUsername",
            email="DifferentEmail@gmail.com",
            hashed_password="Password12345",
        )
        self.repo.add(new_user)

        new_user.email = valid_user_entity.email

        with pytest.raises(UserAlreadyExists):
            self.repo.save(new_user)

    def test_save_duplicate_username(self, valid_user_entity):
        self.repo.add(valid_user_entity)

        new_user = self.get_user_entity(
            username="DifferentUsername",
            email="DifferentEmail@gmail.com",
            hashed_password="Password12345",
        )
        self.repo.add(new_user)

        new_user.username = valid_user_entity.username

        with pytest.raises(UserAlreadyExists):
            self.repo.save(new_user)

    def test_save_nonexistent_user(self, valid_user_entity):
        with pytest.raises(UserNotFound):
            self.repo.save(valid_user_entity)

    def test_delete_success(self, valid_user_entity):
        self.repo.add(valid_user_entity)

        self.repo.delete(valid_user_entity.id)

        assert not self.repo.exists_by_id(valid_user_entity.id)

    def test_delete_nonexistent_user(self, valid_user_entity):
        with pytest.raises(UserNotFound):
            self.repo.delete(valid_user_entity.id)

    def test_get_by_id_returns_correct_user(self, valid_user_entity):
        self.repo.add(valid_user_entity)

        user = self.repo.get_by_id(valid_user_entity.id)

        assert user.id == valid_user_entity.id
        assert user.username == valid_user_entity.username
        assert user.email == valid_user_entity.email
        assert user.password.value == valid_user_entity.password.value

    def test_get_by_id_nonexistent_user_raises_error(self):
        with pytest.raises(UserNotFound):
            self.repo.get_by_id(ID())

    def test_get_by_email_returns_correct_user(self, valid_user_entity):
        self.repo.add(valid_user_entity)

        user = self.repo.get_by_email(valid_user_entity.email)

        assert user.id == valid_user_entity.id
        assert user.username == valid_user_entity.username
        assert user.email == valid_user_entity.email
        assert user.password.value == valid_user_entity.password.value

    def test_get_by_email_nonexistent_user_raises_error(self):
        with pytest.raises(UserNotFound):
            self.repo.get_by_email(Email("nonexistent.mail@test.com"))

    def test_exists_by_id_returns_true_for_existing_user(self, valid_user_entity):
        self.repo.add(valid_user_entity)

        result = self.repo.exists_by_id(valid_user_entity.id)
        assert result

    def test_exists_by_id_returns_false_for_nonexistent_user(self):
        result = self.repo.exists_by_id(ID())
        assert not result

    def test_exists_by_email_returns_true_for_existing_user(self, valid_user_entity):
        self.repo.add(valid_user_entity)

        result = self.repo.exists_by_email(valid_user_entity.email)
        assert result

    def test_exists_by_email_returns_false_for_nonexistent_user(self):
        result = self.repo.exists_by_email(Email("nonexistent.mail@test.com"))
        assert not result
