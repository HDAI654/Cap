from sqlalchemy import or_, select
from sqlalchemy.exc import (
    IntegrityError,
    OperationalError,
    SQLAlchemyError,
    TimeoutError,
)
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.trade_record import TradeRecord
from src.domain.ports.trade_repository import TradeRepository
from src.exceptions import (
    DatabaseConnectionError,
    DatabaseOperationError,
    DatabaseTimeoutError,
    TradeNotFoundError,
)
from src.infrastructure.persistence.mappers import model_to_trade, trade_to_model
from src.infrastructure.persistence.models import TradeModel


class SQLAlchemyTradeRepository(TradeRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, trade: TradeRecord) -> None:
        self._session.add(trade_to_model(trade))
        await self._execute("add_trade", self._session.flush)

    async def get_by_id(self, trade_id: str) -> TradeRecord:
        result = await self._execute(
            "get_trade",
            self._session.execute,
            select(TradeModel).where(TradeModel.trade_id == trade_id),
        )
        model = result.scalar_one_or_none()
        if model is None:
            raise TradeNotFoundError(f"Trade '{trade_id}' does not exist.")
        return model_to_trade(model)

    async def list_by_trader(self, trader_id: str) -> list[TradeRecord]:
        result = await self._execute(
            "list_trades_by_trader",
            self._session.execute,
            select(TradeModel)
            .where(
                or_(
                    TradeModel.buyer_id == trader_id,
                    TradeModel.seller_id == trader_id,
                )
            )
            .order_by(TradeModel.executed_at.desc()),
        )
        return [model_to_trade(m) for m in result.scalars().all()]

    async def list_by_instrument(self, instrument_id: str) -> list[TradeRecord]:
        result = await self._execute(
            "list_trades_by_instrument",
            self._session.execute,
            select(TradeModel)
            .where(TradeModel.instrument_id == instrument_id)
            .order_by(TradeModel.executed_at.desc()),
        )
        return [model_to_trade(m) for m in result.scalars().all()]

    async def exists(self, trade_id: str) -> bool:
        result = await self._execute(
            "trade_exists",
            self._session.execute,
            select(TradeModel.trade_id).where(TradeModel.trade_id == trade_id),
        )
        return result.scalar_one_or_none() is not None

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
