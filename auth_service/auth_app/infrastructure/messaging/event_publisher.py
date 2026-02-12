from typing import Any, Dict
from confluent_kafka import Producer
from auth_app.domain.value_objects.id import ID
from auth_app.domain.value_objects.username import Username
from auth_app.domain.value_objects.email import Email
from auth_app.domain.value_objects.device import Device
import json
import logging

logger = logging.getLogger(__name__)


class EventPublisher:
    def __init__(self, producer: Producer, default_topic: str):
        self._producer = producer
        self._default_topic = default_topic

    def publish(
        self, event: str, data: Dict[str, Any], topic: str | None = None
    ) -> None:
        """
        Publish an event to Kafka.
        """
        payload = {"event": event, "data": data}
        target_topic = topic or self._default_topic

        try:
            self._producer.produce(
                target_topic, value=json.dumps(payload), callback=self._delivery_report
            )
            self._producer.flush()
            logger.info("Published event %s to topic %s", event, target_topic)
        except Exception as e:
            logger.exception("Failed to publish Kafka event: %s", e)

    @staticmethod
    def _delivery_report(err: Exception | None, msg: Any):
        if err:
            logger.error("Message delivery failed: %s", err)
        else:
            logger.info("Message delivered to %s [%d]", msg.topic(), msg.partition())

    def publish_user_created(self, user_id: ID, username: Username, email: Email):
        self.publish(
            "user_created", {"id": user_id.value, "username": username.value, "email": email.value}
        )

    def publish_user_logged_in(
        self, user_id: ID, username: Username, device: Device, session_id: ID
    ):
        self.publish(
            "user_logged_in",
            {
                "id": user_id.value,
                "username": username.value,
                "device": device.value,
                "session_id": session_id.value,
            },
        )
    
    def publish_user_logged_out(
        self, user_id: ID, username: Username, device: Device, session_id: ID
    ):
        self.publish(
            "user_logged_out",
            {
                "id": user_id.value,
                "username": username.value,
                "device": device.value,
                "session_id": session_id.value,
            },
        )
