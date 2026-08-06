import logging
from dataclasses import dataclass
import bcrypt
from src.conf import Config
from src.domain.entities.session import Session
from src.domain.events.user_logged_in import UserLoggedIn
from src.domain.ports.event_publisher import EventPublisher
from src.domain.ports.password_hasher import PasswordHasher
from src.domain.ports.session_repository import SessionRepository
from src.domain.ports.token_encoder import TokenEncoder
from src.domain.ports.unit_of_work import UnitOfWork
from src.domain.value_objects.email import Email
from src.domain.value_objects.role import Role
from src.exceptions import InvalidEmailOrPasswordError

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class AdminLoginCommand:
    email: str
    password: str
    admin_password: str
    device: str


@dataclass(frozen=True, slots=True)
class AdminLoginResult:
    access_token: str
    refresh_token: str


class AdminLoginHandler:
    """Issue ADMIN-role tokens after account + admin-secret checks."""

    def __init__(
        self,
        uow: UnitOfWork,
        session_repository: SessionRepository,
        token_encoder: TokenEncoder,
        password_hasher: PasswordHasher,
        event_publisher: EventPublisher | None = None,
    ) -> None:
        self._uow = uow
        self._sessions = session_repository
        self._tokens = token_encoder
        self._hasher = password_hasher
        self._events = event_publisher

    async def handle(self, command: AdminLoginCommand) -> AdminLoginResult:
        logger.info("Admin login attempt: email=%s", command.email)

        admin_hash = (Config.ADMIN_PASSWORD_HASH or "").strip()
        if not admin_hash:
            logger.warning("ADMIN_PASSWORD_HASH is not configured")
            raise InvalidEmailOrPasswordError()

        email = Email(command.email)
        try:
            async with self._uow:
                user = await self._uow.users.get_by_email(email)
        except Exception as exc:
            raise InvalidEmailOrPasswordError() from exc

        if not self._hasher.verify(command.password, user.hashed_password):
            raise InvalidEmailOrPasswordError()

        if not self._verify_admin_password(command.admin_password, admin_hash):
            logger.warning("Admin password mismatch for email=%s", command.email)
            raise InvalidEmailOrPasswordError()

        role = Role.admin()
        session = Session.create(user_id=user.id.value, device=command.device)
        await self._sessions.add(session)

        access = self._tokens.create_access_token(
            user.id, session.id, session.device, role
        )
        refresh = self._tokens.create_refresh_token(
            user.id, session.id, session.device, role
        )

        if self._events is not None:
            await self._events.publish(
                UserLoggedIn(
                    user_id=user.id.value,
                    email=user.email.value,
                    session_id=session.id.value,
                    device=session.device.value,
                    role=role.value,
                )
            )

        logger.info("Admin login success: user_id=%s", user.id.value)
        return AdminLoginResult(access_token=access, refresh_token=refresh)

    @staticmethod
    def _verify_admin_password(plain: str, hashed: str) -> bool:
        if not plain or not hashed:
            return False
        try:
            return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
        except Exception:
            return False
