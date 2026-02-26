from rest_framework.permissions import BasePermission
from auth_app.infrastructure.security.jwt_tools import JWT_Tools


class IsAuthenticatedJWT(BasePermission):
    def has_permission(self, request, view):
        # Detect client type
        client_type = request.headers.get("X-Client")
        if not client_type:
            client_type = request.headers.get("User-Agent", "unknown")
        client_type = str(client_type).lower()

        if client_type == "android" or client_type == "ios":
            # Mobile apps use Authorization header
            auth_header = request.META.get("HTTP_AUTHORIZATION", "")
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
                try:
                    JWT_Tools.decode_token(token)
                    return True
                except:
                    return False
        else:
            # Web uses cookies
            access_token = request.COOKIES.get("access")
            if access_token:
                try:
                    JWT_Tools.decode_token(access_token)
                    return True
                except:
                    return False

        return False
