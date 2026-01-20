import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from auth_app.service.signup_service import SignupService
from auth_app.infrastructure.persistence.repositories.user_repository import (
    DjangoUserRepository,
)
from auth_app.infrastructure.cache.redis_client import get_redis_client
from auth_app.infrastructure.cache.session_repository import RedisSessionRepository
from auth_app.infrastructure.messaging.kafka_producer import get_producer
from auth_app.infrastructure.messaging.event_publisher import EventPublisher
from auth_app.infrastructure.security.jwt_tools import JWT_Tools
from auth_app.infrastructure.security.password_hasher import PasswordHasher
from core.response_utils import ResponseProducer
from auth_app.api.v1.serializers import SignupSerializer

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name="dispatch")
class SignupView(APIView):
    """
    Signup endpoint.
    """

    def post(self, request):
        logger.info("Signup started.")
        serializer = SignupSerializer(data=request.data)

        if not serializer.is_valid():
            logger.debug(f"Signup validation failed: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        username = data["username"]
        email = data["email"]
        password = data["password"]
        device = str(request.headers.get("User-Agent", "unknown"))

        redis_client = get_redis_client()
        kafka_producer = get_producer()

        user_repo = DjangoUserRepository()
        session_repo = RedisSessionRepository(redis_client=redis_client)
        event_publisher = EventPublisher(kafka_producer=kafka_producer)
        jwt_tools = JWT_Tools()
        password_hasher = PasswordHasher()

        signup_service = SignupService(
            user_repo=user_repo,
            session_repo=session_repo,
            event_publisher=event_publisher,
            jwt_tools=jwt_tools,
            password_hasher=password_hasher,
        )

        access_token, refresh_token = signup_service.execute(
            username=username, email=email, password=password, device=device
        )

        response = ResponseProducer.build_response_with_tokens(
            request=request,
            access_token=access_token,
            refresh_token=refresh_token,
            message="User registered successfully.",
        )

        logger.info("Signup finished successfully.")

        return response
