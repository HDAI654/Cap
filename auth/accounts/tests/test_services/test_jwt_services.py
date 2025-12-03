from django.test import TestCase
from django.conf import settings
import jwt
from datetime import datetime, timedelta
from ...services.jwt_service import JWT_Tools


class JWTToolsTestCase(TestCase):

    def setUp(self):
        # Override settings for tests
        settings.ACCESS_TOKEN_EXPIRE_MINUTES = 1
        settings.REFRESH_TOKEN_EXPIRE_DAYS = 1
        settings.JWT_SECRET = "testsecret123"
        settings.JWT_ALGORITHM = "HS256"

    def test_create_access_token(self):
        user_id = 42
        username = "testuser"
        token = JWT_Tools.create_access_token(user_id, username)
        self.assertIsInstance(token, str)

        decoded = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        self.assertEqual(decoded["sub"], user_id)
        self.assertEqual(decoded["username"], username)
        self.assertEqual(decoded["type"], "access")
        self.assertIn("exp", decoded)
        self.assertGreater(datetime.utcfromtimestamp(decoded["exp"]), datetime.utcnow())

    def test_create_refresh_token(self):
        user_id = 42
        username = "testuser"
        session_id = "session_abc123"
        token = JWT_Tools.create_refresh_token(user_id, username, session_id)
        self.assertIsInstance(token, str)

        decoded = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        self.assertEqual(decoded["sub"], user_id)
        self.assertEqual(decoded["username"], username)
        self.assertEqual(decoded["sid"], session_id)
        self.assertEqual(decoded["type"], "refresh")
        self.assertIn("exp", decoded)
        self.assertGreater(datetime.utcfromtimestamp(decoded["exp"]), datetime.utcnow())

    def test_decode_token(self):
        user_id = 1
        username = "decode_test"
        token = JWT_Tools.create_access_token(user_id, username)
        decoded = JWT_Tools.decode_token(token)
        self.assertEqual(decoded["sub"], user_id)
        self.assertEqual(decoded["username"], username)
        self.assertEqual(decoded["type"], "access")

    def test_invalid_token(self):
        invalid_token = "this.is.not.a.jwt"
        with self.assertRaises(jwt.exceptions.DecodeError):
            JWT_Tools.decode_token(invalid_token)

    def test_expired_token(self):
        # Create a token that is already expired
        past_time = datetime.utcnow() - timedelta(minutes=10)
        payload = {
            "sub": 1,
            "username": "expired_user",
            "exp": past_time,
            "type": "access",
        }
        token = jwt.encode(
            payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
        )

        with self.assertRaises(jwt.exceptions.ExpiredSignatureError):
            JWT_Tools.decode_token(token)
