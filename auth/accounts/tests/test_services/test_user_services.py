"""from django.test import TestCase
from accounts.services.user_services import signup_user
from django.contrib.auth.models import User
from unittest.mock import patch

class UserServiceTest(TestCase):
    @patch("accounts.services.user_services.publish_user_created")
    def test_signup_user_creates_user(self, mock_publish):
        user = signup_user("serviceuser", "service@example.com", "strongpassword")

        self.assertEqual(user.username, "serviceuser")
        self.assertTrue(User.objects.filter(username="serviceuser").exists())

        # ensures Kafka function was triggered, but no real connection happens
        mock_publish.assert_called_once()
"""
