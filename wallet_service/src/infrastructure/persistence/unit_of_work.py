from types import TracebackType
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from src.domain.ports.unit_of_work import UnitOfWork
from src.infrastructure.persistence.repositories.sqlalchemy_wallet_repository import (
    SQLAlchemyWalletRepository,
)


class SQLAlchemyUnitOfWork(UnitOfWork):
    """Coordinates a single transactional boundary over wallet repositories."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory
        self._session: AsyncSession | None = None
        self.wallets: SQLAlchemyWalletRepository

    async def __aenter__(self) -> "SQLAlchemyUnitOfWork":
        """Open a new session and bind repositories."""
        self._session = self._session_factory()
        self.wallets = SQLAlchemyWalletRepository(self._session)
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
        if self._session is None:
            raise RuntimeError("UnitOfWork session is not active.")
        await self._session.commit()

    async def rollback(self) -> None:
        """Rollback the current transaction."""
        if self._session is None:
            raise RuntimeError("UnitOfWork session is not active.")
        await self._session.rollback()
