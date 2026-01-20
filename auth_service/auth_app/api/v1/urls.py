from django.urls import path
from auth_app.api.v1.signup import SignupView
from auth_app.api.v1.login import LoginView
from auth_app.api.v1.logout import LogoutView
from auth_app.api.v1.rotation import RotationView
from auth_app.api.v1.revoke import RevokeView

urlpatterns = [
    path("signup/", SignupView.as_view(), name="signup"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("rotation/", RotationView.as_view(), name="rotation"),
    path("revoke/", RevokeView.as_view(), name="revoke"),
]
