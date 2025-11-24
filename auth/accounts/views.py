import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import SignupSerializer
from .services.user_services import signup_user

logger = logging.getLogger(__name__)


class SignupView(APIView):
    """
    API endpoint for user signup.
    """

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            try:
                user = signup_user(
                    username=data["username"],
                    email=data["email"],
                    password=data["password"],
                )
                logger.info(f"Signup successful for user_id={user.id}")
                return Response(
                    {"message": "User created successfully"},
                    status=status.HTTP_201_CREATED,
                )
            except Exception as e:
                logger.error(f"Error during signup: {e}", exc_info=True)
                return Response(
                    {"error": "Failed to create user"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        else:
            logger.warning(f"Signup validation failed: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
