"""import jwt
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from unittest.mock import patch
from django.conf import settings
from datetime import datetime, timedelta

# -------------------------------------------------------------------------
# SIGNUP TESTS
# -------------------------------------------------------------------------
class SignupViewTest(APITestCase):
    def setUp(self):
        self.url = reverse("signup")

    @patch("accounts.services.user_services.publish_user_created")
    def test_user_creation(self, mock_publish):
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

    @patch("accounts.services.user_services.publish_user_created")
    def test_signup_android_success(self, mock_publish):
        data = {
            "username": "James",
            "email": "James@test.com",
            "password": "strongpass123"
        }

        response = self.client.post(self.url, data, HTTP_X_CLIENT="android")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("access_token", response.data)
        self.assertIn("refresh_token", response.data)
        mock_publish.assert_called_once()

    @patch("accounts.services.user_services.publish_user_created")
    def test_signup_web_success_sets_cookies(self, mock_publish):
        data = {
            "username": "James2",
            "email": "James2@test.com",
            "password": "strongpass123"
        }

        response = self.client.post(self.url, data)  # no X-Client → default web

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("access", response.cookies)
        self.assertIn("refresh", response.cookies)
        mock_publish.assert_called_once()

# -------------------------------------------------------------------------
# LOGIN TESTS
# -------------------------------------------------------------------------
class LoginViewTest(APITestCase):
    def setUp(self):
        self.url = reverse("login")

    def create_user(self):
        return User.objects.create_user(
            username="Jimmy",
            email="test@example.com",
            password="testpass123"
        )

    def test_login_android_success(self):
        self.create_user()

        response = self.client.post(
            self.url,
            {"username": "Jimmy", "password": "testpass123"},
            HTTP_X_CLIENT="android"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_web_sets_cookies(self):
        self.create_user()

        response = self.client.post(
            self.url,
            {"username": "testuser", "password": "testpass123"}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.cookies)
        self.assertIn("refresh", response.cookies)

    def test_login_invalid_credentials(self):
        response = self.client.post(
            self.url,
            {"username": "wrong", "password": "nope"}
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("error", response.data)

# -------------------------------------------------------------------------
# REFRESH TOKEN TESTS
# -------------------------------------------------------------------------
class AuthTests(APITestCase):
    def setUp(self):
        self.url = reverse("token_refresh")

    def create_user(self):
        return User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

    def test_refresh_android_success(self):
        user = self.create_user()

        # create manual refresh token
        refresh = jwt.encode(
            {
                "sub": user.id,
                "type": "refresh",
                "exp": datetime.utcnow() + timedelta(days=1)
            },
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM
        )


        response = self.client.post(
            self.url,
            {"refresh": refresh},
            HTTP_X_CLIENT="android"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_refresh_web_success(self):
        user = self.create_user()

        refresh = jwt.encode(
            {
                "sub": user.id,
                "type": "refresh",
                "exp": datetime.utcnow() + timedelta(days=1)
            },
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM
        )

        self.client.cookies["refresh"] = refresh


        response = self.client.post(self.url)  # web request

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.cookies)

    def test_refresh_missing_token(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_invalid_token(self):
        response = self.client.post(
            self.url,
            {"refresh": "invalid"},
            HTTP_X_CLIENT="android"
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch("jwt.decode")
    def test_refresh_expired_token(self, mock_decode):
        mock_decode.side_effect = jwt.ExpiredSignatureError()


        response = self.client.post(
            self.url,
            {"refresh": "dummy"},
            HTTP_X_CLIENT="android"
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["error"], "Refresh token expired")

    def test_refresh_wrong_type_token(self):
        user = self.create_user()

        bad_token = jwt.encode(
            {
                "sub": user.id,
                "type": "access",  # ❌ should be refresh
                "exp": datetime.utcnow() + timedelta(hours=1)
            },
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM
        )



        response = self.client.post(
            self.url,
            {"refresh": bad_token},
            HTTP_X_CLIENT="android"
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("Invalid", response.data["error"])
"""
