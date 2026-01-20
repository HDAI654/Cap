import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from auth_app.service.token_rotation_service import TokenRotationService
from auth_app.infrastructure.persistence.repositories.user_repository import (
    DjangoUserRepository,
)
from auth_app.infrastructure.cache.redis_client import get_redis_client
from auth_app.infrastructure.cache.session_repository import RedisSessionRepository
from auth_app.infrastructure.security.jwt_tools import JWT_Tools
from core.response_utils import ResponseProducer
from auth_app.api.v1.serializers import RotationSerializer

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name="dispatch")
class RotationView(APIView):
    """
    Rotation endpoint.
    """

    def post(self, request):
        logger.info("Rotation started.")
        serializer = RotationSerializer(data=request.data)

        if not serializer.is_valid():
            logger.debug(f"Rotation validation failed: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        device = str(request.headers.get("User-Agent", "unknown"))
        if device == "android":
            refresh_token = data.get("refresh")
        else:
            refresh_token = request.COOKIES.get("refresh")

        redis_client = get_redis_client

        user_repo = DjangoUserRepository()
        session_repo = RedisSessionRepository(redis_client=redis_client)
        jwt_tools = JWT_Tools()

        rotation_service = TokenRotationService(
            user_repo=user_repo, session_repo=session_repo, jwt_tools=jwt_tools
        )

        access_token, refresh_token = rotation_service.execute(
            refresh_token=refresh_token, device=device
        )

        response = ResponseProducer.build_response_with_tokens(
            request=request,
            access_token=access_token,
            refresh_token=refresh_token,
            message="Rotation finished successfully.",
        )

        logger.info("Rotation finished successfully.")

        return response
