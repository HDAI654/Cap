import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from auth_app.service.del_account_service import DelAccountService
from auth_app.infrastructure.persistence.repositories.user_repository import (
    DjangoUserRepository,
)
from auth_app.infrastructure.cache.redis_client import get_redis_client
from auth_app.infrastructure.cache.session_repository import RedisSessionRepository
from auth_app.infrastructure.messaging.kafka_producer import get_producer
from auth_app.infrastructure.messaging.event_publisher import EventPublisher
from auth_app.infrastructure.security.jwt_tools import JWT_Tools
from auth_app.api.v1.serializers import DelAccountSerializer
from core.exceptions import AuthenticationFailed

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name="dispatch")
class DelAccountView(APIView):
    """
    Delete account endpoint.
    """

    def post(self, request):
        try:
            logger.info("Deleting account started.")
            serializer = DelAccountSerializer(data=request.data)

            if not serializer.is_valid():
                logger.debug(f"DelAccount validation failed: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            data = serializer.validated_data
            device = request.headers.get("X-Client")
            if not device:
                device = request.headers.get("User-Agent", "unknown")
            device = str(device).lower()

            if device == "android":
                refresh_token = data.get("refresh")
                if refresh_token is None:
                    return Response(
                        data={
                            "success": False,
                            "error": "Refresh token is required in request body",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            else:
                refresh_token = request.COOKIES.get("refresh")
                if refresh_token is None:
                    return Response(
                        data={
                            "success": False,
                            "error": "Refresh token is required in cookies",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            redis_client = get_redis_client()
            kafka_producer = get_producer()

            user_repo = DjangoUserRepository()
            session_repo = RedisSessionRepository(redis_client=redis_client)
            jwt_tools = JWT_Tools()
            event_publisher = EventPublisher(
                producer=kafka_producer, default_topic="user-events"
            )

            logout_service = DelAccountService(
                user_repo=user_repo,
                session_repo=session_repo,
                event_publisher=event_publisher,
                jwt_tools=jwt_tools,
            )

            logout_service.execute(
                refresh_token=refresh_token,
            )

            logger.info("Deleting account finished successfully.")

            response = Response(
                {"message": "Account deleted out successfully."}, status=status.HTTP_200_OK
            )

            if device != "android":
                response.delete_cookie("access")
                response.delete_cookie("refresh")

            return response

        except AuthenticationFailed as e:
            return Response(
                data={"success": False, "error": str(e)},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        except Exception as e:
            logger.exception("Failed to delete account - unexpected error")
            return Response(
                data={"success": False, "error": "INTERNAL_SERVER_ERROR"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
