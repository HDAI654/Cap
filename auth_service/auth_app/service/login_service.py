from auth_app.domain.ports.session_repository import SessionRepository
from auth_app.domain.repositories.user_repository import UserRepository
from auth_app.domain.factories.session_factory import SessionFactory
from auth_app.infrastructure.messaging.event_publisher import EventPublisher
from auth_app.domain.value_objects.email import Email
from auth_app.infrastructure.security.jwt_tools import JWT_Tools
from auth_app.infrastructure.security.password_hasher import PasswordHasher
from core.exceptions import AuthenticationFailed


class LoginService:
    def __init__(
        self,
        user_repo: UserRepository,
        session_repo: SessionRepository,
        event_publisher: EventPublisher,
        jwt_tools: JWT_Tools,
        password_hasher: PasswordHasher,
    ):
        self.user_repo = user_repo
        self.session_repo = session_repo
        self.event_publisher = event_publisher
        self.jwt_tools = jwt_tools
        self.password_hasher = password_hasher

    def execute(self, username: str, email: str, password: str, device: str):
        user = self.user_repo.get_by_email(email=Email(email))
        if not self.password_hasher.verify(password, user.password.value):
            raise AuthenticationFailed("The password is incorrect")
        if user.username != username:
            raise AuthenticationFailed("This username is not for this user")

        session = SessionFactory.create(user_id=user.id.value, device=device)
        self.session_repo.add(session)

        self.event_publisher.publish_user_logged_in(
            user_id=user.id,
            username=user.username,
            device=session.device,
            session_id=session.id,
        )

        access_token = self.jwt_tools.create_access_token(user.id, user.username)
        refresh_token = self.jwt_tools.create_refresh_token(
            user.id, user.username, session.id
        )

        return access_token, refresh_token
