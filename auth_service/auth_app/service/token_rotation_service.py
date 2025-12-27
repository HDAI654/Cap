from ..infrastructure.security.jwt_tools import JWT_Tools
from ...core.exceptions import InvalidTokenError
from ..repository.user_repository import UserRepo
from ..infrastructure.cache.session import SessionManager


class TokenRotationService:
    def __init__(
        self, user_repo: UserRepo, session_manager: SessionManager, refresh_token
    ):
        self.user_repo = user_repo
        self.session_manager = session_manager
        self.refresh_token = refresh_token

    def execute(self):
        payload = JWT_Tools.decode_token(self.refresh_token)
        required_claims = {"sub", "sid", "type"}
        if not required_claims.issubset(payload) or payload.get("type") != "refresh":
            raise InvalidTokenError("Refresh token is invalid or has wrong type")

        user = self.user_repo.get_by_id(id=payload["sub"])

        session = SessionManager.get_session(payload["sid"])
        if session.user_id != user.id:
            raise InvalidTokenError("Refresh token is invalid or has wrong data")

        new_access = JWT_Tools.create_access_token(user.id, user.username)

        # Check need for rotate refresh token
        need = JWT_Tools.should_rotate_refresh_token(payload["exp"])
        if need:
            new_refresh = JWT_Tools.create_refresh_token(
                user.id, user.username, session.id
            )
            return new_access, new_refresh

        return new_access
