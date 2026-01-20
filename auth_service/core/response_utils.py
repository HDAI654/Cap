from rest_framework.response import Response
from django.conf import settings


class ResponseProducer:
    @staticmethod
    def build_response_with_tokens(
        request, access_token, refresh_token=None, message="OK"
    ):
        client_type = request.headers.get("X-Client", "web").lower()

        # ANDROID → return tokens as JSON
        if client_type == "android":
            if refresh_token is None:
                return Response(
                    {"access": access_token, "message": message}, status=200
                )
            return Response(
                {"access": access_token, "refresh": refresh_token, "message": message},
                status=200,
            )

        # WEB → set cookies
        response = Response({"message": message}, status=200)

        access_age = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        refresh_age = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600

        response.set_cookie(
            "access",
            access_token,
            httponly=True,
            secure=not settings.DEBUG,
            samesite="Lax",
            max_age=access_age,
        )
        if refresh_token is not None:
            response.set_cookie(
                "refresh",
                refresh_token,
                httponly=True,
                secure=not settings.DEBUG,
                samesite="Lax",
                max_age=refresh_age,
            )

        return response
