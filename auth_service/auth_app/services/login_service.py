from ..infrastructure.cache.session import SessionManager
from..repository.user_repository import UserRepo
from ..infrastructure.messaging.event_publisher import EventPublisher
from ..domain.user import UserEntity
from ..infrastructure.security.jwt_tools import JWT_Tools

class LoginService:
    def __init__(self, user_repo: UserRepo, session_manager: SessionManager, event_publisher: EventPublisher):
        self.user_repo = user_repo
        self.session_manager = session_manager
        self.event_publisher = event_publisher
        
    def execute(self, username: str, password: str, device: str):
        user = UserEntity(username=username, password=password)
        user = self.user_repo.authenticate(user)

        session = self.session_manager.new_session(user_id=user.id, device=device)
        session.save()

        self.event_publisher.publish_user_logged_in(user_id=user.id, username=user.username, device=device, session_id=session.id)

        access_token = JWT_Tools.create_access_token(user.id, user.username)
        refresh_token = JWT_Tools.create_refresh_token(
            user.id, user.username, session.id
        )

        return access_token, refresh_token