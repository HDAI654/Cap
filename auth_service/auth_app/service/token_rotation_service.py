from core.exceptions import InvalidTokenError
from auth_app.infrastructure.cache.session_repository import SessionRepository
from auth_app.domain.factories.session_factory import SessionFactory
from auth_app.domain.repositories.user_repository import UserRepository
from auth_app.infrastructure.security.jwt_tools import JWT_Tools
from auth_app.domain.value_objects.id import ID
from auth_app.domain.value_objects.datetime import DateTime


class TokenRotationService:
    def __init__(
        self,
        user_repo: UserRepository,
        session_repo: SessionRepository,
        jwt_tools: JWT_Tools,
    ):
        self.user_repo = user_repo
        self.session_repo = session_repo
        self.jwt_tools = jwt_tools

    def execute(self, refresh_token: str, device: str):
        payload = self.jwt_tools.decode_token(refresh_token)
        required_claims = {"sub", "sid", "type"}
        if not required_claims.issubset(payload) or payload.get("type") != "refresh":
            raise InvalidTokenError("Refresh token is invalid or has wrong type")
        
        try:
            exp = float(payload["exp"])
        except:
            raise InvalidTokenError("Refresh token is invalid or has wrong data")

        user = self.user_repo.get_by_id(id=ID(payload["sub"]))

        session = self.session_repo.get_by_id(ID(payload["sid"]))
        if session.user_id != user.id:
            raise InvalidTokenError("Refresh token is invalid or has wrong data")
        self.session_repo.delete(id=session.id, user_id=session.user_id)
        session = SessionFactory.create(user_id=user.id.value, device=device)
        self.session_repo.add(session)

        new_access = self.jwt_tools.create_access_token(
            user.id, user.username
        )

        need = self.jwt_tools.should_rotate_refresh_token(DateTime(exp))
        if need:
            new_refresh = self.jwt_tools.create_refresh_token(
                user.id, user.username, session.id
            )
            return new_access, new_refresh

        return new_access, None
