import logging

from src.application.DTOs.instrument import InstrumentDTO
from src.application.get_instrument import _to_dto
from src.domain.ports.unit_of_work import UnitOfWork

logger = logging.getLogger(__name__)


class ListInstrumentsHandler:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def handle(self) -> list[InstrumentDTO]:
        logger.info("Listing instruments")
        async with self._uow:
            instruments = await self._uow.instruments.list_all()
        return [_to_dto(i) for i in instruments]
