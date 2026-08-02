import logging
from dataclasses import dataclass
from decimal import Decimal

from src.domain.factories.instrument_factory import InstrumentFactory
from src.domain.ports.unit_of_work import UnitOfWork
from src.domain.value_objects.currency import Currency
from src.domain.value_objects.money import Money
from src.domain.value_objects.quantity import Quantity
from src.exceptions import (
    InstrumentAlreadyExistsError,
    InvalidInstrumentParametersError,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class CreateInstrumentCommand:
    symbol: str
    name: str
    tick_size: Decimal
    lot_size: int
    minimum_order_quantity: int
    maximum_order_quantity: int
    currency: str
    total_shares: int = 0


@dataclass(frozen=True, slots=True)
class CreateInstrumentResult:
    instrument_id: str


class CreateInstrumentHandler:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def handle(self, command: CreateInstrumentCommand) -> CreateInstrumentResult:
        logger.info("Creating instrument: symbol=%s", command.symbol)

        try:
            currency = Currency(command.currency)
        except ValueError as exc:
            raise InvalidInstrumentParametersError(
                f"Invalid currency: {command.currency}"
            ) from exc

        async with self._uow:
            existing = await self._uow.instruments.get_by_symbol(
                command.symbol.strip().upper()
            )
            if existing is not None:
                raise InstrumentAlreadyExistsError(
                    f"Instrument with symbol '{command.symbol}' already exists."
                )

            instrument = InstrumentFactory.create(
                symbol=command.symbol,
                name=command.name,
                tick_size=Money(command.tick_size, currency),
                lot_size=Quantity(command.lot_size),
                minimum_order_quantity=Quantity(command.minimum_order_quantity),
                maximum_order_quantity=Quantity(command.maximum_order_quantity),
                currency=currency,
                total_shares=Quantity(command.total_shares),
            )
            await self._uow.instruments.add(instrument)
            await self._uow.commit()
            instrument.clear_changes()

        logger.info(
            "Instrument created: id=%s symbol=%s",
            instrument.id.value,
            instrument.symbol,
        )
        return CreateInstrumentResult(instrument_id=instrument.id.value)
