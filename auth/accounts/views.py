import logging
import jwt

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from django.conf import settings
from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .serializers import SignupSerializer

from .services.user_services import create_user
from .services.jwt_service import JWT_Tools
from .services.response_services import TokenResponseService
from .services.session_service import SessionManager


logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name="dispatch")
class SignupView(APIView):
    """
    Signup endpoint with JWT support for Web & Mobile.
    """

    def post(self, request):
        serializer = SignupSerializer(data=request.data)

        if not serializer.is_valid():
            logger.warning(f"Signup validation failed: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            data = serializer.validated_data
            user = create_user(
                username=data["username"],
                email=data["email"],
                password=data["password"],
            )

            logger.info(f"Signup successful for user_id={user.id}")

            user_agent = str(request.headers.get("User-Agent", "unknown"))

            session = SessionManager.new_session(user_id=user.id, device=user_agent)
            session.save()

            access_token = JWT_Tools.create_access_token(user.id, user.username)
            refresh_token = JWT_Tools.create_refresh_token(
                user.id, user.username, session.id
            )

            return TokenResponseService.build_response(
                request,
                access_token,
                refresh_token,
                message="User created successfully",
            )

        except Exception as e:
            logger.error(f"Error during signup: {e}", exc_info=True)
            return Response(
                {"error": "Failed to create user"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@method_decorator(csrf_exempt, name="dispatch")
class LoginView(APIView):
    """
    Login endpoint for Web & Android.
    """

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        user = authenticate(username=username, password=password)
        if not user:
            return Response(
                {"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
            )

        logger.info(f"Login successful for user_id={user.id}")

        access_token = JWT_Tools.create_access_token(user.id, user.username)
        refresh_token = JWT_Tools.create_refresh_token(user.id)

        return TokenResponseService.build_response(
            request, access_token, refresh_token, message="User created successfully"
        )


@method_decorator(csrf_exempt, name="dispatch")
class RefreshTokenView(APIView):
    """
    Refresh access token for Web (cookie) & Android (JSON).
    """

    def post(self, request):
        client_type = request.headers.get("X-Client", "web").lower()

        # ANDROID → refresh token in JSON body
        if client_type == "android":
            refresh_token = request.data.get("refresh")
        else:
            # WEB → refresh token in HttpOnly cookie
            refresh_token = request.COOKIES.get("refresh")

        if not refresh_token:
            return Response(
                {"error": "Refresh token missing"}, status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            payload = JWT_Tools.decode_token(refresh_token)

            if payload["type"] != "refresh":
                return Response(
                    {"error": "Invalid refresh token"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            new_access = JWT_Tools.create_access_token(payload["sub"], "unknown")

            # ANDROID → return new access token in JSON
            if client_type == "android":
                return Response({"access": new_access})

            # WEB → send new access token in cookie
            response = Response({"message": "Token refreshed"})
            max_age = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

            response.set_cookie(
                "access",
                new_access,
                httponly=True,
                secure=True,
                samesite="Lax",
                max_age=max_age,
            )
            return response

        except jwt.ExpiredSignatureError:
            return Response(
                {"error": "Refresh token expired"}, status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            logger.error(f"Refresh error: {e}", exc_info=True)
            return Response(
                {"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED
            )
