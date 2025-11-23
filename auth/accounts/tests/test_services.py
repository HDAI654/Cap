from django.test import TestCase
from services.user_services import signup_user
from django.contrib.auth.models import User

class UserServiceTest(TestCase):
    def test_signup_user_creates_user(self):
        user = signup_user("serviceuser", "service@example.com", "strongpassword")
        self.assertEqual(user.username, "serviceuser")
        self.assertTrue(User.objects.filter(username="serviceuser").exists())
