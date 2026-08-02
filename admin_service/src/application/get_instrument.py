import logging
from dataclasses import dataclass

from src.application.DTOs.instrument import InstrumentDTO
from src.domain.entities.instrument import Instrument
from src.domain.ports.unit_of_work import UnitOfWork
from src.domain.value_objects.instrument_id import InstrumentId

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class GetInstrumentQuery:
    instrument_id: str


class GetInstrumentHandler:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def handle(self, query: GetInstrumentQuery) -> InstrumentDTO:
        logger.info("Getting instrument: id=%s", query.instrument_id)
        async with self._uow:
            instrument = await self._uow.instruments.get_by_id(
                InstrumentId(query.instrument_id)
            )
        return _to_dto(instrument)


def _to_dto(instrument: Instrument) -> InstrumentDTO:
    return InstrumentDTO(
        instrument_id=instrument.id.value,
        symbol=instrument.symbol,
        name=instrument.name,
        tick_size=instrument.tick_size.amount,
        tick_size_currency=instrument.tick_size.currency.value,
        lot_size=instrument.lot_size.value,
        minimum_order_quantity=instrument.minimum_order_quantity.value,
        maximum_order_quantity=instrument.maximum_order_quantity.value,
        currency=instrument.currency.value,
        total_shares=instrument.total_shares.value,
        status=instrument.status.value,
        created_at=instrument.created_at,
        updated_at=instrument.updated_at,
    )
