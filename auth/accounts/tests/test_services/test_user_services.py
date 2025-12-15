import pytest
from django.contrib.auth.models import User
from accounts.services.user_services import create_user


@pytest.mark.django_db
def test_create_user_creates_user(mocker):
    # Mock Kafka publisher
    mock_publish = mocker.patch("accounts.services.user_services.publish_user_created")

    user = create_user(
        username="serviceuser",
        email="service@example.com",
        password="strongpassword",
    )

    # --- Assertions ---
    assert user.username == "serviceuser"
    assert User.objects.filter(username="serviceuser").exists()

    # Kafka publish was triggered (but no real connection)
    mock_publish.assert_called_once()
