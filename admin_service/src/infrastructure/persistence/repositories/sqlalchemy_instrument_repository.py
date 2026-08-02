import logging

from sqlalchemy import select
from sqlalchemy.exc import (
    IntegrityError,
    OperationalError,
    SQLAlchemyError,
    TimeoutError,
)
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.instrument import Instrument
from src.domain.ports.instrument_repository import InstrumentRepository
from src.domain.value_objects.instrument_id import InstrumentId
from src.exceptions import (
    DatabaseConnectionError,
    DatabaseOperationError,
    DatabaseTimeoutError,
    InstrumentNotFoundError,
)
from src.infrastructure.persistence.mappers import (
    instrument_to_model,
    model_to_instrument,
)
from src.infrastructure.persistence.models import InstrumentModel

logger = logging.getLogger(__name__)


class SQLAlchemyInstrumentRepository(InstrumentRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, instrument: Instrument) -> None:
        self._session.add(instrument_to_model(instrument))
        await self._execute("add_instrument", self._session.flush)

    async def get_by_id(self, instrument_id: InstrumentId) -> Instrument:
        result = await self._execute(
            "get_instrument_by_id",
            self._session.execute,
            select(InstrumentModel).where(InstrumentModel.id == instrument_id.value),
        )
        model = result.scalar_one_or_none()
        if model is None:
            raise InstrumentNotFoundError(
                f"Instrument '{instrument_id.value}' does not exist."
            )
        return model_to_instrument(model)

    async def get_by_symbol(self, symbol: str) -> Instrument | None:
        result = await self._execute(
            "get_instrument_by_symbol",
            self._session.execute,
            select(InstrumentModel).where(InstrumentModel.symbol == symbol.upper()),
        )
        model = result.scalar_one_or_none()
        return model_to_instrument(model) if model is not None else None

    async def update(self, instrument: Instrument) -> None:
        result = await self._execute(
            "get_instrument_for_update",
            self._session.execute,
            select(InstrumentModel).where(InstrumentModel.id == instrument.id.value),
        )
        model = result.scalar_one_or_none()
        if model is None:
            raise InstrumentNotFoundError(
                f"Instrument '{instrument.id.value}' does not exist."
            )
        if instrument.is_status_changed():
            model.status = instrument.status.value
        if instrument.is_shares_changed():
            model.total_shares = instrument.total_shares.value
        if instrument.is_changed():
            model.updated_at = instrument.updated_at

    async def list_all(self) -> list[Instrument]:
        result = await self._execute(
            "list_instruments",
            self._session.execute,
            select(InstrumentModel).order_by(InstrumentModel.symbol.asc()),
        )
        return [model_to_instrument(m) for m in result.scalars().all()]

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
