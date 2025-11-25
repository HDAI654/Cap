import logging
import jwt
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import SignupSerializer
from .services.user_services import signup_user
from .services.jwt_service import create_access_token, create_refresh_token, decode_token
from django.conf import settings
from django.contrib.auth import authenticate

logger = logging.getLogger(__name__)


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

            user = signup_user(
                username=data["username"],
                email=data["email"],
                password=data["password"],
            )

            logger.info(f"Signup successful for user_id={user.id}")

            access_token = create_access_token(user.id, user.username)
            refresh_token = create_refresh_token(user.id)

            client_type = request.headers.get("X-Client", "web").lower()
            response_data = {"message": "User created successfully"}

            # Android client → tokens returned as JSON
            if client_type == "android":
                response_data["access_token"] = access_token
                response_data["refresh_token"] = refresh_token
                return Response(response_data, status=status.HTTP_201_CREATED)

            # Web client → tokens stored in secure cookies
            response = Response(response_data, status=status.HTTP_201_CREATED)

            access_max_age = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
            refresh_max_age = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600

            response.set_cookie(
                "access",
                access_token,
                httponly=True,
                secure=True,
                samesite="Strict",
                max_age=access_max_age,
            )

            response.set_cookie(
                "refresh",
                refresh_token,
                httponly=True,
                secure=True,
                samesite="Strict",
                max_age=refresh_max_age,
            )

            return response

        except Exception as e:
            logger.error(f"Error during signup: {e}", exc_info=True)
            return Response(
                {"error": "Failed to create user"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

class LoginView(APIView):
    """
    Login endpoint for Web & Android.
    """

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        user = authenticate(username=username, password=password)
        if not user:
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        logger.info(f"Login successful for user_id={user.id}")

        access = create_access_token(user.id, user.username)
        refresh = create_refresh_token(user.id)

        client_type = request.headers.get("X-Client", "web").lower()

        # ANDROID → return tokens in JSON
        if client_type == "android":
            return Response({
                "access": access,
                "refresh": refresh
            }, status=status.HTTP_200_OK)

        # WEB → send tokens in cookies
        response = Response({"message": "Login successful"}, status=status.HTTP_200_OK)

        access_age = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        refresh_age = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400

        response.set_cookie(
            "access", access, httponly=True, secure=True, samesite="Strict", max_age=access_age
        )
        response.set_cookie(
            "refresh", refresh, httponly=True, secure=True, samesite="Strict", max_age=refresh_age
        )

        return response

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
            return Response({"error": "Refresh token missing"}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            payload = decode_token(refresh_token)

            if payload["type"] != "refresh":
                return Response({"error": "Invalid refresh token"}, status=status.HTTP_401_UNAUTHORIZED)

            new_access = create_access_token(payload["sub"], "unknown")

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
                samesite="Strict",
                max_age=max_age,
            )
            return response

        except jwt.ExpiredSignatureError:
            return Response({"error": "Refresh token expired"}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            logger.error(f"Refresh error: {e}", exc_info=True)
            return Response({"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
