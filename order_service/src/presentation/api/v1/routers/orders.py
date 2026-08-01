import logging
from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query, Response, status

from src.application.cancel_order import CancelOrderCommand, CancelOrderHandler
from src.application.expire_order import ExpireOrderCommand, ExpireOrderHandler
from src.application.fill_order import FillOrderCommand, FillOrderHandler
from src.application.get_order import GetOrderHandler, GetOrderQuery
from src.application.list_orders_by_trader import (
    ListOrdersByTraderHandler,
    ListOrdersByTraderQuery,
)
from src.application.open_order import OpenOrderCommand, OpenOrderHandler
from src.application.reject_order import RejectOrderCommand, RejectOrderHandler
from src.application.submit_order import (
    SubmitOrderCommand,
    SubmitOrderHandler,
)
from src.exceptions import (
    DatabaseConnectionError,
    DatabaseOperationError,
    DatabaseTimeoutError,
    InvalidIdempotencyKeyError,
    InvalidInstrumentIdError,
    InvalidOrderFillError,
    InvalidOrderIdError,
    InvalidOrderParametersError,
    InvalidOrderStateError,
    InvalidQuantityError,
    InvalidTraderIdError,
    MessagingConnectionError,
    MessagingPublishError,
    OrderAlreadyExistsError,
    OrderNotFoundError,
)
from src.presentation.api.v1.schemas.requests import (
    FillOrderRequest,
    SubmitOrderRequest,
)
from src.presentation.api.v1.schemas.responses import (
    OrderResponse,
    SubmitOrderResponse,
)
from src.presentation.dependencies import EventPublisherDep, UoWFactory

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/orders", tags=["orders"])

OrderIdPath = Annotated[
    str,
    Path(
        ...,
        min_length=36,
        max_length=36,
        description="Order UUID v4 identifier.",
    ),
]


def _order_response_from_dto(dto) -> OrderResponse:
    return OrderResponse(
        order_id=dto.order_id,
        trader_id=dto.trader_id,
        instrument_id=dto.instrument_id,
        side=dto.side,
        order_type=dto.order_type,
        time_in_force=dto.time_in_force,
        quantity=dto.quantity,
        filled_quantity=dto.filled_quantity,
        remaining_quantity=dto.remaining_quantity,
        limit_price=dto.limit_price,
        limit_price_currency=dto.limit_price_currency,
        status=dto.status,
        idempotency_key=dto.idempotency_key,
        created_at=dto.created_at,
        updated_at=dto.updated_at,
    )


# ---------------------------------------------------------------------------
# Submit / query
# ---------------------------------------------------------------------------


@router.post(
    "",
    response_model=SubmitOrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit an order",
)
async def submit_order(
    body: SubmitOrderRequest,
    uow_factory: UoWFactory,
    event_publisher: EventPublisherDep,
) -> SubmitOrderResponse:
    """Submit a new order for a trader."""
    logger.info(
        "Submitting order: trader_id=%s, instrument_id=%s, side=%s, type=%s",
        body.trader_id,
        body.instrument_id,
        body.side,
        body.order_type,
    )
    handler = SubmitOrderHandler(uow_factory(), event_publisher)
    try:
        result = await handler.handle(
            SubmitOrderCommand(
                trader_id=body.trader_id,
                instrument_id=body.instrument_id,
                side=body.side,
                order_type=body.order_type,
                time_in_force=body.time_in_force,
                quantity=body.quantity,
                idempotency_key=body.idempotency_key,
                limit_price=body.limit_price,
                limit_price_currency=body.limit_price_currency,
            ),
        )
    except OrderAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc) or "Order already exists.",
        )
    except (
        InvalidTraderIdError,
        InvalidInstrumentIdError,
        InvalidIdempotencyKeyError,
        InvalidQuantityError,
        InvalidOrderParametersError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc) or "Invalid request data.",
        )
    except (
        DatabaseConnectionError,
        DatabaseTimeoutError,
        MessagingConnectionError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc) or "Service temporarily unavailable.",
        )
    except (DatabaseOperationError, MessagingPublishError) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc) or "Operation failed.",
        )
    except Exception:
        logger.exception("Unexpected error while submitting order")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )

    logger.info("Order submitted: order_id=%s", result.order_id)
    return SubmitOrderResponse(order_id=result.order_id)


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    status_code=status.HTTP_200_OK,
    summary="Get an order",
)
async def get_order(
    order_id: OrderIdPath,
    uow_factory: UoWFactory,
) -> OrderResponse:
    """Retrieve an order by identifier."""
    logger.info("Retrieving order: order_id=%s", order_id)
    handler = GetOrderHandler(uow_factory())
    try:
        dto = await handler.handle(GetOrderQuery(order_id=order_id))
    except OrderNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc) or "Order not found.",
        )
    except InvalidOrderIdError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc) or "Invalid order id.",
        )
    except (DatabaseConnectionError, DatabaseTimeoutError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc) or "Database temporarily unavailable.",
        )
    except DatabaseOperationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc) or "Database operation failed.",
        )
    except Exception:
        logger.exception("Unexpected error while retrieving order")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )

    logger.info("Order retrieved: order_id=%s, status=%s", dto.order_id, dto.status)
    return _order_response_from_dto(dto)


@router.get(
    "",
    response_model=list[OrderResponse],
    status_code=status.HTTP_200_OK,
    summary="List orders by trader",
)
async def list_orders_by_trader(
    uow_factory: UoWFactory,
    trader_id: Annotated[
        str,
        Query(..., min_length=36, max_length=36, description="Trader UUID v4."),
    ],
) -> list[OrderResponse]:
    """Return all orders placed by the given trader."""
    logger.info("Listing orders for trader: trader_id=%s", trader_id)
    handler = ListOrdersByTraderHandler(uow_factory())
    try:
        dtos = await handler.handle(ListOrdersByTraderQuery(trader_id=trader_id))
    except InvalidTraderIdError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc) or "Invalid trader id.",
        )
    except (DatabaseConnectionError, DatabaseTimeoutError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc) or "Database temporarily unavailable.",
        )
    except DatabaseOperationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc) or "Database operation failed.",
        )
    except Exception:
        logger.exception("Unexpected error while listing orders")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )

    logger.info("Orders listed: trader_id=%s, count=%s", trader_id, len(dtos))
    return [_order_response_from_dto(dto) for dto in dtos]


# ---------------------------------------------------------------------------
# Lifecycle transitions
# ---------------------------------------------------------------------------


@router.post(
    "/{order_id}/open",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Open an order",
)
async def open_order(
    order_id: OrderIdPath,
    uow_factory: UoWFactory,
    event_publisher: EventPublisherDep,
) -> Response:
    """Accept a NEW order onto the book (NEW → OPEN)."""
    logger.info("Opening order: order_id=%s", order_id)
    handler = OpenOrderHandler(uow_factory(), event_publisher)
    try:
        await handler.handle(OpenOrderCommand(order_id=order_id))
    except OrderNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc) or "Order not found.",
        )
    except InvalidOrderStateError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc) or "Order is not in a valid state.",
        )
    except InvalidOrderIdError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc) or "Invalid order id.",
        )
    except (
        DatabaseConnectionError,
        DatabaseTimeoutError,
        MessagingConnectionError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc) or "Service temporarily unavailable.",
        )
    except (DatabaseOperationError, MessagingPublishError) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc) or "Operation failed.",
        )
    except Exception:
        logger.exception("Unexpected error while opening order")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )

    logger.info("Order opened: order_id=%s", order_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{order_id}/fills",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Fill an order",
)
async def fill_order(
    order_id: OrderIdPath,
    body: FillOrderRequest,
    uow_factory: UoWFactory,
    event_publisher: EventPublisherDep,
) -> Response:
    """Apply a fill against the remaining quantity of an order."""
    logger.info(
        "Filling order: order_id=%s, fill_quantity=%s",
        order_id,
        body.fill_quantity,
    )
    handler = FillOrderHandler(uow_factory(), event_publisher)
    try:
        await handler.handle(
            FillOrderCommand(order_id=order_id, fill_quantity=body.fill_quantity),
        )
    except OrderNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc) or "Order not found.",
        )
    except InvalidOrderStateError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc) or "Order is not in a valid state.",
        )
    except (
        InvalidOrderIdError,
        InvalidQuantityError,
        InvalidOrderFillError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc) or "Invalid request data.",
        )
    except (
        DatabaseConnectionError,
        DatabaseTimeoutError,
        MessagingConnectionError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc) or "Service temporarily unavailable.",
        )
    except (DatabaseOperationError, MessagingPublishError) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc) or "Database operation failed.",
        )
    except Exception:
        logger.exception("Unexpected error while filling order")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )

    logger.info(
        "Order filled: order_id=%s, fill_quantity=%s",
        order_id,
        body.fill_quantity,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{order_id}/cancel",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel an order",
)
async def cancel_order(
    order_id: OrderIdPath,
    uow_factory: UoWFactory,
    event_publisher: EventPublisherDep,
) -> Response:
    """Cancel an active order."""
    logger.info("Cancelling order: order_id=%s", order_id)
    handler = CancelOrderHandler(uow_factory(), event_publisher)
    try:
        await handler.handle(CancelOrderCommand(order_id=order_id))
    except OrderNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc) or "Order not found.",
        )
    except InvalidOrderStateError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc) or "Order is not in a valid state.",
        )
    except InvalidOrderIdError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc) or "Invalid order id.",
        )
    except (
        DatabaseConnectionError,
        DatabaseTimeoutError,
        MessagingConnectionError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc) or "Service temporarily unavailable.",
        )
    except (DatabaseOperationError, MessagingPublishError) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc) or "Operation failed.",
        )
    except Exception:
        logger.exception("Unexpected error while cancelling order")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )

    logger.info("Order cancelled: order_id=%s", order_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{order_id}/reject",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Reject an order",
)
async def reject_order(
    order_id: OrderIdPath,
    uow_factory: UoWFactory,
    event_publisher: EventPublisherDep,
) -> Response:
    """Reject a NEW order."""
    logger.info("Rejecting order: order_id=%s", order_id)
    handler = RejectOrderHandler(uow_factory(), event_publisher)
    try:
        await handler.handle(RejectOrderCommand(order_id=order_id))
    except OrderNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc) or "Order not found.",
        )
    except InvalidOrderStateError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc) or "Order is not in a valid state.",
        )
    except InvalidOrderIdError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc) or "Invalid order id.",
        )
    except (
        DatabaseConnectionError,
        DatabaseTimeoutError,
        MessagingConnectionError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc) or "Service temporarily unavailable.",
        )
    except (DatabaseOperationError, MessagingPublishError) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc) or "Operation failed.",
        )
    except Exception:
        logger.exception("Unexpected error while rejecting order")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )

    logger.info("Order rejected: order_id=%s", order_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{order_id}/expire",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Expire an order",
)
async def expire_order(
    order_id: OrderIdPath,
    uow_factory: UoWFactory,
    event_publisher: EventPublisherDep,
) -> Response:
    """Expire an order that is still on the book."""
    logger.info("Expiring order: order_id=%s", order_id)
    handler = ExpireOrderHandler(uow_factory(), event_publisher)
    try:
        await handler.handle(ExpireOrderCommand(order_id=order_id))
    except OrderNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc) or "Order not found.",
        )
    except InvalidOrderStateError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc) or "Order is not in a valid state.",
        )
    except InvalidOrderIdError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc) or "Invalid order id.",
        )
    except (
        DatabaseConnectionError,
        DatabaseTimeoutError,
        MessagingConnectionError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc) or "Service temporarily unavailable.",
        )
    except (DatabaseOperationError, MessagingPublishError) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc) or "Operation failed.",
        )
    except Exception:
        logger.exception("Unexpected error while expiring order")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )

    logger.info("Order expired: order_id=%s", order_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
