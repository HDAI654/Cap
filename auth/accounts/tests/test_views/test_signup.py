'''from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from unittest.mock import patch
import fakeredis
from django.contrib.auth import get_user_model
import jwt
from django.conf import settings
from ...services.jwt_service import JWT_Tools
from auth.accounts.services.user_services import publish_user_created

User = get_user_model()


class SignupViewTests(TestCase):
    """
    Tests for SignupView.
    """

    def setUp(self):
        self.client = APIClient()
        self.url = reverse("signup")
        # Patch the function
        self.fake_redis = fakeredis.FakeStrictRedis()
        patcher = patch(
            "auth.accounts.services.session_service.redis_client", self.fake_redis
        )
        self.mock_redis = patcher.start()
        self.addCleanup(patcher.stop)

         # --- Patch Kafka globally ---
        get_producer_patcher = patch(
            "auth.accounts.services.kafka_producer.get_producer",
            return_value=None 
        )
        self.mock_get_producer = get_producer_patcher.start()
        self.addCleanup(get_producer_patcher.stop)


        self.valid_payload = {
            "username": "testuser",
            "email": "testuser@example.com",
            "password": "StrongPassword123!",
        }
    def test_signup_success(self):
        response = self.client.post(
            self.url,
            data=self.valid_payload,
            format="json",
            HTTP_USER_AGENT="pytest-agent",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # --- User created ---
        self.assertTrue(
            User.objects.filter(
                username=self.valid_payload["username"],
                email=self.valid_payload["email"],
            ).exists()
        )

        # --- Tokens exist ---
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

        # --- Tokens valid ---
        access_payload = JWT_Tools.decode_token(response.data["access"])
        refresh_payload = JWT_Tools.decode_token(response.data["refresh"])

        self.assertEqual(access_payload["username"], "testuser")
        self.assertEqual(access_payload["user_id"], refresh_payload["user_id"])

        # --- Session stored ---
        self.assertTrue(self.mock_redis.set.called)


    def test_signup_validation_error(self):
        """
        Invalid payload returns 400 and serializer errors.
        """

        invalid_payload = {
            "username": "",
            "email": "invalid-email",
            "password": "",
        }

        response = self.client.post(
            self.url,
            data=invalid_payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIsInstance(response.data, dict)

    @patch("auth.accounts.services.user_services.create_user")
    def test_signup_internal_error(self, mock_create_user):
        """
        Any unexpected exception returns HTTP 500.
        """

        mock_create_user.side_effect = Exception("DB failure")

        response = self.client.post(
            self.url,
            data=self.valid_payload,
            format="json",
        )

        self.assertEqual(
            response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        self.assertEqual(response.data, {"error": "Failed to create user"})

    def test_signup_requires_post_method(self):
        """
        GET method should not be allowed.
        """

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
 '''