import logging

from fastapi import APIRouter, HTTPException, Request, status

from src.application.deliver_notification import (
    DeliverNotificationCommand,
    DeliverNotificationHandler,
)
from src.exceptions import InvalidNotificationError
from src.presentation.schemas import (
    PushNotificationRequest,
    PushNotificationResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/internal/v1", tags=["internal"])


@router.post(
    "/notifications",
    response_model=PushNotificationResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Internal: push notification to connected traders",
)
async def push_notification(
    body: PushNotificationRequest,
    request: Request,
) -> PushNotificationResponse:
    hub = request.app.state.connection_hub
    handler = DeliverNotificationHandler(hub)
    try:
        delivered = await handler.handle(
            DeliverNotificationCommand(
                event_type=body.event_type,
                recipient_trader_ids=body.recipient_trader_ids,
                payload=body.payload,
            )
        )
    except InvalidNotificationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        )
    except Exception:
        logger.exception("Failed to deliver notification")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deliver notification.",
        )
    return PushNotificationResponse(delivered=delivered)
