from rest_framework.response import Response
from django.conf import settings


class TokenResponseService:
    @staticmethod
    def build_response(request, access, refresh, message="OK"):
        client_type = request.headers.get("X-Client", "web").lower()

        # ANDROID → return tokens as JSON
        if client_type == "android":
            return Response(
                {"access": access, "refresh": refresh, "message": message}, status=200
            )

        # WEB → set cookies
        response = Response({"message": message}, status=200)

        access_age = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        refresh_age = settings.ACCESS_TOKEN_EXPIRE_DAYS * 24 * 3600

        response.set_cookie(
            "access",
            access,
            httponly=True,
            secure=True,
            samesite="Lax",
            max_age=access_age,
        )
        response.set_cookie(
            "refresh",
            refresh,
            httponly=True,
            secure=True,
            samesite="Lax",
            max_age=refresh_age,
        )

        return response
