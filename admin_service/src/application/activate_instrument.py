import logging
from dataclasses import dataclass

from src.domain.ports.unit_of_work import UnitOfWork
from src.domain.value_objects.instrument_id import InstrumentId

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ActivateInstrumentCommand:
    instrument_id: str


class ActivateInstrumentHandler:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def handle(self, command: ActivateInstrumentCommand) -> None:
        logger.info("Activating instrument: id=%s", command.instrument_id)
        async with self._uow:
            instrument = await self._uow.instruments.get_by_id(
                InstrumentId(command.instrument_id)
            )
            instrument.activate()
            if instrument.is_changed():
                await self._uow.instruments.update(instrument)
                await self._uow.commit()
                instrument.clear_changes()
        logger.info("Instrument activated: id=%s", command.instrument_id)
