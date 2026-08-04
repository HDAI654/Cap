import logging
from types import TracebackType
from sqlalchemy.exc import OperationalError, SQLAlchemyError, TimeoutError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.domain.ports.unit_of_work import UnitOfWork
from src.exceptions import (
    DatabaseConnectionError,
    DatabaseOperationError,
    DatabaseTimeoutError,
)
from src.infrastructure.persistence.repositories.sqlalchemy_order_repository import (
    SQLAlchemyOrderRepository,
)

logger = logging.getLogger(__name__)


class SQLAlchemyUnitOfWork(UnitOfWork):
    """Coordinates a single transactional boundary over order repositories."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory
        self._session: AsyncSession | None = None
        self.orders: SQLAlchemyOrderRepository

    async def __aenter__(self) -> "SQLAlchemyUnitOfWork":
        """Open a new session and bind repositories."""
        self._session = self._session_factory()
        self.orders = SQLAlchemyOrderRepository(self._session)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        """Rollback on failure and always close the session."""
        if self._session is None:
            return

        try:
            if exc_type is not None:
                await self.rollback()
        finally:
            await self._session.close()
            self._session = None

    async def commit(self) -> None:
        """Commit the current transaction."""
        logger.debug("Committing transaction")

        await self._execute_db_operation(
            "commit",
            self._session.commit,
        )

        logger.debug("Transaction committed successfully")

    async def rollback(self) -> None:
        """Rollback the current transaction."""
        logger.debug("Rolling back transaction")

        await self._execute_db_operation(
            "rollback",
            self._session.rollback,
        )

        logger.debug("Transaction rolled back successfully")

    async def _execute_db_operation(self, operation: str, coro, *args, **kwargs):
        """Generic wrapper for database operations with error handling."""
        try:
            return await coro(*args, **kwargs)
        except OperationalError as e:
            logger.exception("Database connection error during %s", operation)
            raise DatabaseConnectionError(f"Failed to connect to database: {e}") from e
        except TimeoutError as e:
            logger.exception("Database timeout during %s", operation)
            raise DatabaseTimeoutError(f"Database operation timed out: {e}") from e
        except SQLAlchemyError as e:
            logger.exception("Database error during %s", operation)
            raise DatabaseOperationError(f"Database operation failed: {e}") from e
