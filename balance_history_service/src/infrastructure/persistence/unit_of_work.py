from types import TracebackType

from sqlalchemy.exc import OperationalError, SQLAlchemyError, TimeoutError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.domain.ports.unit_of_work import UnitOfWork
from src.exceptions import (
    DatabaseConnectionError,
    DatabaseOperationError,
    DatabaseTimeoutError,
)
from src.infrastructure.persistence.repositories.sqlalchemy_order_history_repository import (
    SQLAlchemyOrderHistoryRepository,
)
from src.infrastructure.persistence.repositories.sqlalchemy_trade_repository import (
    SQLAlchemyTradeRepository,
)


class SQLAlchemyUnitOfWork(UnitOfWork):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory
        self._session: AsyncSession | None = None
        self.trades: SQLAlchemyTradeRepository
        self.order_history: SQLAlchemyOrderHistoryRepository

    async def __aenter__(self) -> "SQLAlchemyUnitOfWork":
        self._session = self._session_factory()
        self.trades = SQLAlchemyTradeRepository(self._session)
        self.order_history = SQLAlchemyOrderHistoryRepository(self._session)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if self._session is None:
            return
        try:
            if exc_type is not None:
                await self.rollback()
        finally:
            await self._session.close()
            self._session = None

    async def commit(self) -> None:
        await self._execute("commit", self._session.commit)

    async def rollback(self) -> None:
        await self._execute("rollback", self._session.rollback)

    async def _execute(self, operation: str, coro, *args, **kwargs):
        try:
            return await coro(*args, **kwargs)
        except OperationalError as e:
            raise DatabaseConnectionError(f"Failed to connect to database: {e}") from e
        except TimeoutError as e:
            raise DatabaseTimeoutError(f"Database operation timed out: {e}") from e
        except SQLAlchemyError as e:
            raise DatabaseOperationError(f"Database operation failed: {e}") from e
