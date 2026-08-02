import logging
from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Response, status

from src.application.activate_instrument import (
    ActivateInstrumentCommand,
    ActivateInstrumentHandler,
)
from src.application.allocate_shares import (
    AllocateSharesCommand,
    AllocateSharesHandler,
)
from src.application.create_instrument import (
    CreateInstrumentCommand,
    CreateInstrumentHandler,
)
from src.application.delist_instrument import (
    DelistInstrumentCommand,
    DelistInstrumentHandler,
)
from src.application.get_instrument import GetInstrumentHandler, GetInstrumentQuery
from src.application.halt_instrument import HaltInstrumentCommand, HaltInstrumentHandler
from src.application.list_instruments import ListInstrumentsHandler
from src.exceptions import (
    DatabaseConnectionError,
    DatabaseOperationError,
    DatabaseTimeoutError,
    InstrumentAlreadyExistsError,
    InstrumentNotFoundError,
    InvalidInstrumentIdError,
    InvalidInstrumentParametersError,
    InvalidInstrumentStateError,
)
from src.presentation.api.v1.schemas.requests import (
    AllocateSharesRequest,
    CreateInstrumentRequest,
)
from src.presentation.api.v1.schemas.responses import (
    CreateInstrumentResponse,
    InstrumentResponse,
)
from src.presentation.auth import AdminClaims
from src.presentation.dependencies import UoWFactory

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/instruments", tags=["instruments"])

InstrumentIdPath = Annotated[
    str,
    Path(..., min_length=36, max_length=36, description="Instrument UUID v4."),
]


def _to_response(dto) -> InstrumentResponse:
    return InstrumentResponse(
        instrument_id=dto.instrument_id,
        symbol=dto.symbol,
        name=dto.name,
        tick_size=dto.tick_size,
        tick_size_currency=dto.tick_size_currency,
        lot_size=dto.lot_size,
        minimum_order_quantity=dto.minimum_order_quantity,
        maximum_order_quantity=dto.maximum_order_quantity,
        currency=dto.currency,
        total_shares=dto.total_shares,
        status=dto.status,
        created_at=dto.created_at,
        updated_at=dto.updated_at,
    )


@router.post(
    "",
    response_model=CreateInstrumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create instrument",
)
async def create_instrument(
    body: CreateInstrumentRequest,
    uow_factory: UoWFactory,
    _claims: AdminClaims,
) -> CreateInstrumentResponse:
    handler = CreateInstrumentHandler(uow_factory())
    try:
        result = await handler.handle(
            CreateInstrumentCommand(
                symbol=body.symbol,
                name=body.name,
                tick_size=body.tick_size,
                lot_size=body.lot_size,
                minimum_order_quantity=body.minimum_order_quantity,
                maximum_order_quantity=body.maximum_order_quantity,
                currency=body.currency,
                total_shares=body.total_shares,
            )
        )
    except InstrumentAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except InvalidInstrumentParametersError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        )
    except (DatabaseConnectionError, DatabaseTimeoutError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        )
    except DatabaseOperationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        )
    except Exception:
        logger.exception("Unexpected error creating instrument")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )
    return CreateInstrumentResponse(instrument_id=result.instrument_id)


@router.get(
    "",
    response_model=list[InstrumentResponse],
    status_code=status.HTTP_200_OK,
    summary="List instruments",
)
async def list_instruments(
    uow_factory: UoWFactory,
    _claims: AdminClaims,
) -> list[InstrumentResponse]:
    handler = ListInstrumentsHandler(uow_factory())
    try:
        dtos = await handler.handle()
    except (DatabaseConnectionError, DatabaseTimeoutError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        )
    except DatabaseOperationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        )
    except Exception:
        logger.exception("Unexpected error listing instruments")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )
    return [_to_response(d) for d in dtos]


@router.get(
    "/{instrument_id}",
    response_model=InstrumentResponse,
    status_code=status.HTTP_200_OK,
    summary="Get instrument",
)
async def get_instrument(
    instrument_id: InstrumentIdPath,
    uow_factory: UoWFactory,
    _claims: AdminClaims,
) -> InstrumentResponse:
    handler = GetInstrumentHandler(uow_factory())
    try:
        dto = await handler.handle(GetInstrumentQuery(instrument_id=instrument_id))
    except InstrumentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except InvalidInstrumentIdError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        )
    except (DatabaseConnectionError, DatabaseTimeoutError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        )
    except DatabaseOperationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        )
    except Exception:
        logger.exception("Unexpected error getting instrument")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )
    return _to_response(dto)


@router.post(
    "/{instrument_id}/activate",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Activate instrument",
)
async def activate_instrument(
    instrument_id: InstrumentIdPath,
    uow_factory: UoWFactory,
    _claims: AdminClaims,
) -> Response:
    handler = ActivateInstrumentHandler(uow_factory())
    try:
        await handler.handle(ActivateInstrumentCommand(instrument_id=instrument_id))
    except InstrumentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except InvalidInstrumentStateError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except InvalidInstrumentIdError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        )
    except (DatabaseConnectionError, DatabaseTimeoutError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        )
    except DatabaseOperationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        )
    except Exception:
        logger.exception("Unexpected error activating instrument")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{instrument_id}/halt",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Halt instrument",
)
async def halt_instrument(
    instrument_id: InstrumentIdPath,
    uow_factory: UoWFactory,
    _claims: AdminClaims,
) -> Response:
    handler = HaltInstrumentHandler(uow_factory())
    try:
        await handler.handle(HaltInstrumentCommand(instrument_id=instrument_id))
    except InstrumentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except InvalidInstrumentStateError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except InvalidInstrumentIdError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        )
    except (DatabaseConnectionError, DatabaseTimeoutError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        )
    except DatabaseOperationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        )
    except Exception:
        logger.exception("Unexpected error halting instrument")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{instrument_id}/delist",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delist instrument",
)
async def delist_instrument(
    instrument_id: InstrumentIdPath,
    uow_factory: UoWFactory,
    _claims: AdminClaims,
) -> Response:
    handler = DelistInstrumentHandler(uow_factory())
    try:
        await handler.handle(DelistInstrumentCommand(instrument_id=instrument_id))
    except InstrumentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except InvalidInstrumentStateError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except InvalidInstrumentIdError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        )
    except (DatabaseConnectionError, DatabaseTimeoutError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        )
    except DatabaseOperationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        )
    except Exception:
        logger.exception("Unexpected error delisting instrument")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{instrument_id}/allocations",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Allocate shares",
)
async def allocate_shares(
    instrument_id: InstrumentIdPath,
    body: AllocateSharesRequest,
    uow_factory: UoWFactory,
    _claims: AdminClaims,
) -> Response:
    handler = AllocateSharesHandler(uow_factory())
    try:
        await handler.handle(
            AllocateSharesCommand(
                instrument_id=instrument_id,
                quantity=body.quantity,
            )
        )
    except InstrumentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except InvalidInstrumentStateError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except (InvalidInstrumentIdError, InvalidInstrumentParametersError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        )
    except (DatabaseConnectionError, DatabaseTimeoutError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        )
    except DatabaseOperationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        )
    except Exception:
        logger.exception("Unexpected error allocating shares")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
