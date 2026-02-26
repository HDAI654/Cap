from rest_framework.throttling import SimpleRateThrottle


class IPBasedThrottle(SimpleRateThrottle):
    """Throttle by IP address for anonymous users"""

    scope = "anon"

    def get_cache_key(self, request, view):
        # Get IP address
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return f"throttle_ip_{ip}"


class JWTUserThrottle(SimpleRateThrottle):
    """Throttle by user ID for authenticated users"""

    scope = "user"

    def get_cache_key(self, request, view):
        # Check if user is authenticated via JWT
        if hasattr(request, "user") and request.user and request.user.is_authenticated:
            return f"throttle_user_{request.user.id}"
        return None  # Don't throttle anonymous with this class
