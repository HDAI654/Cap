from core.exceptions import BadRequestError, UserAlreadyExists
from auth_app.domain.ports.session_repository import SessionRepository
from auth_app.domain.repositories.user_repository import UserRepository
from auth_app.infrastructure.messaging.event_publisher import EventPublisher
from auth_app.domain.factories.user_factory import UserFactory
from auth_app.domain.factories.session_factory import SessionFactory
from auth_app.infrastructure.security.jwt_tools import JWT_Tools
from auth_app.infrastructure.security.password_hasher import PasswordHasher


class SignupService:
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
        hashed_password = self.password_hasher.hash(str(password))
        try:
            user = UserFactory.create(
                username=username, email=email, hashed_password=hashed_password
            )
        except (TypeError, ValueError) as e:
            raise BadRequestError(str(e))
        try:
            self.user_repo.add(user)
        except UserAlreadyExists as e:
            raise BadRequestError(str(e))

        self.event_publisher.publish_user_created(
            user_id=user.id, username=user.username, email=user.email
        )

        try:
            session = SessionFactory.create(user_id=user.id.value, device=device)
        except (TypeError, ValueError) as e:
            raise BadRequestError(str(e))
        self.session_repo.add(session)

        access_token = self.jwt_tools.create_access_token(user.id, user.username)
        refresh_token = self.jwt_tools.create_refresh_token(
            user.id, user.username, session.id
        )

        return access_token, refresh_token
