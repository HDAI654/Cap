import logging
from dataclasses import dataclass

from src.domain.ports.unit_of_work import UnitOfWork
from src.domain.value_objects.instrument_id import InstrumentId
from src.domain.value_objects.quantity import Quantity

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class AllocateSharesCommand:
    instrument_id: str
    quantity: int


class AllocateSharesHandler:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def handle(self, command: AllocateSharesCommand) -> None:
        logger.info(
            "Allocating shares: instrument_id=%s quantity=%s",
            command.instrument_id,
            command.quantity,
        )
        async with self._uow:
            instrument = await self._uow.instruments.get_by_id(
                InstrumentId(command.instrument_id)
            )
            instrument.allocate_shares(Quantity(command.quantity))
            if instrument.is_changed():
                await self._uow.instruments.update(instrument)
                await self._uow.commit()
                instrument.clear_changes()
        logger.info(
            "Shares allocated: instrument_id=%s quantity=%s",
            command.instrument_id,
            command.quantity,
        )
