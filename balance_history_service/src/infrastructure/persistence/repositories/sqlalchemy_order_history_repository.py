from sqlalchemy import select
from sqlalchemy.exc import (
    IntegrityError,
    OperationalError,
    SQLAlchemyError,
    TimeoutError,
)
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.order_history_entry import OrderHistoryEntry
from src.domain.ports.order_history_repository import OrderHistoryRepository
from src.exceptions import (
    DatabaseConnectionError,
    DatabaseOperationError,
    DatabaseTimeoutError,
)
from src.infrastructure.persistence.mappers import entry_to_model, model_to_entry
from src.infrastructure.persistence.models import OrderHistoryModel


class SQLAlchemyOrderHistoryRepository(OrderHistoryRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, entry: OrderHistoryEntry) -> None:
        self._session.add(entry_to_model(entry))
        await self._execute("add_order_history", self._session.flush)

    async def list_by_order(self, order_id: str) -> list[OrderHistoryEntry]:
        result = await self._execute(
            "list_order_history_by_order",
            self._session.execute,
            select(OrderHistoryModel)
            .where(OrderHistoryModel.order_id == order_id)
            .order_by(OrderHistoryModel.occurred_at.asc()),
        )
        return [model_to_entry(m) for m in result.scalars().all()]

    async def list_by_trader(self, trader_id: str) -> list[OrderHistoryEntry]:
        result = await self._execute(
            "list_order_history_by_trader",
            self._session.execute,
            select(OrderHistoryModel)
            .where(OrderHistoryModel.trader_id == trader_id)
            .order_by(OrderHistoryModel.occurred_at.desc()),
        )
        return [model_to_entry(m) for m in result.scalars().all()]

    async def _execute(self, operation: str, coro, *args, **kwargs):
        try:
            return await coro(*args, **kwargs)
        except IntegrityError as e:
            raise DatabaseOperationError(f"Database integrity error: {e}") from e
        except OperationalError as e:
            raise DatabaseConnectionError(f"Failed to connect to database: {e}") from e
        except TimeoutError as e:
            raise DatabaseTimeoutError(f"Database operation timed out: {e}") from e
        except SQLAlchemyError as e:
            raise DatabaseOperationError(f"Database operation failed: {e}") from e
