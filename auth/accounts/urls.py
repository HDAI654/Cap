from django.urls import path
from .views import SignupView
from .views import LoginView
from .views import RefreshTokenView

urlpatterns = [
    path("signup/", SignupView.as_view(), name="signup"),
    path("login/", LoginView.as_view(), name="login"),
    path("refresh/", RefreshTokenView.as_view(), name="token_refresh"),
]
