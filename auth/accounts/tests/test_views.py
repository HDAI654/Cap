from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from unittest.mock import patch


class SignupViewTest(APITestCase):
    def setUp(self):
        self.url = reverse("signup")

    @patch("accounts.services.user_services.publish_user_created")
    def test_signup_success(self, mock_publish):
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "strongpassword123",
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username="testuser").exists())

        # ensures Kafka function was triggered, but no real connection happens
        mock_publish.assert_called_once()

    @patch("accounts.services.user_services.publish_user_created")
    def test_signup_validation_error(self, mock_publish):
        data = {"username": "", "email": "not-an-email", "password": "short"}  # Invalid data
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)