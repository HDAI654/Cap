from core.exceptions import InvalidTokenError
from auth_app.infrastructure.cache.session_repository import SessionRepository
from auth_app.domain.repositories.user_repository import UserRepository
from auth_app.infrastructure.messaging.event_publisher import EventPublisher
from auth_app.infrastructure.security.jwt_tools import JWT_Tools
from auth_app.domain.value_objects.id import ID


class LogoutService:
    def __init__(
        self,
        user_repo: UserRepository,
        session_repo: SessionRepository,
        event_publisher: EventPublisher,
        jwt_tools: JWT_Tools,
    ):
        self.user_repo = user_repo
        self.session_repo = session_repo
        self.event_publisher = event_publisher
        self.jwt_tools = jwt_tools

    def execute(self, refresh_token: str):
        payload = self.jwt_tools.decode_token(refresh_token)
        required_claims = {"sub", "sid", "type"}
        if not required_claims.issubset(payload) or payload.get("type") != "refresh":
            raise InvalidTokenError("Refresh token is invalid or has wrong type")

        user = self.user_repo.get_by_id(id=ID(payload["sub"]))

        session = self.session_repo.get_by_id(ID(payload["sid"]))
        session_device = session.device
        if session.user_id != user.id:
            raise InvalidTokenError("Refresh token is invalid or has wrong data")
        self.session_repo.delete(id=session.id, user_id=session.user_id)

        self.event_publisher.publish_user_logged_out(
            user_id=user.id,
            username=user.username,
            device=session_device,
            session_id=session.id,
        )
