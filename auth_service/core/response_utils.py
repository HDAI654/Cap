from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from core.exceptions import ResponseProducerError


class ResponseProducer:
    @staticmethod
    def build_response_with_tokens(
        request, access_token, refresh_token=None, message="OK"
    ):
        try:
            client_type = request.headers.get("X-Client")
            if not client_type:
                client_type = request.headers.get("User-Agent", "unknown")
            client_type = str(client_type).lower()

            # ANDROID/IOS → return tokens as JSON
            if client_type == "android" or client_type == "ios":
                if refresh_token is None:
                    return Response(
                        {"access": access_token, "message": message},
                        status=status.HTTP_200_OK,
                    )
                return Response(
                    {
                        "access": access_token,
                        "refresh": refresh_token,
                        "message": message,
                    },
                    status=status.HTTP_200_OK,
                )

            # WEB → set cookies
            response = Response({"message": message}, status=status.HTTP_200_OK)

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
        except Exception as e:
            raise ResponseProducerError(
                f"Unexpected error occurred during response generation:\n{str(e)}"
            ) from e
