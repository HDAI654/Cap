import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from auth_app.service.logout_service import LogoutService
from auth_app.infrastructure.persistence.repositories.user_repository import (
    DjangoUserRepository,
)
from auth_app.infrastructure.cache.redis_client import get_redis_client
from auth_app.infrastructure.cache.session_repository import RedisSessionRepository
from auth_app.infrastructure.security.jwt_tools import JWT_Tools
from auth_app.api.v1.serializers import LogoutSerializer

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name="dispatch")
class LogoutView(APIView):
    """
    Logout endpoint.
    """

    def post(self, request):
        logger.info("Logout started.")
        serializer = LogoutSerializer(data=request.data)

        if not serializer.is_valid():
            logger.debug(f"Logout validation failed: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        device = str(request.headers.get("User-Agent", "unknown"))
        if device == "android":
            refresh_token = data.get("refresh")
        else:
            refresh_token = request.COOKIES.get("refresh")

        redis_client = get_redis_client()

        user_repo = DjangoUserRepository()
        session_repo = RedisSessionRepository(redis_client=redis_client)
        jwt_tools = JWT_Tools()

        logout_service = LogoutService(
            user_repo=user_repo, session_repo=session_repo, jwt_tools=jwt_tools
        )

        logout_service.execute(
            refresh_token=refresh_token,
        )

        logger.info("Logout finished successfully.")

        return Response(
            {"message": "User logged out successfully."}, status=status.HTTP_200_OK
        )
