from typing import Any

from pydantic import BaseModel, Field


class PushNotificationRequest(BaseModel):
    """Internal request body from Notification Dispatcher."""

    event_type: str = Field(..., min_length=1)
    recipient_trader_ids: list[str] = Field(..., min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)


class PushNotificationResponse(BaseModel):
    delivered: int
