import json
import pytest
from unittest.mock import MagicMock
from auth_app.infrastructure.messaging.event_publisher import EventPublisher
from auth_app.domain.value_objects.id import ID
from auth_app.domain.value_objects.username import Username
from auth_app.domain.value_objects.email import Email
from auth_app.domain.value_objects.device import Device


class TestEventPublisher:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.mock_producer = MagicMock()
        self.publisher = EventPublisher(
            self.mock_producer, default_topic="default-topic"
        )

    def test_publish_sends_payload_to_default_topic(self):
        data = {"foo": "bar"}
        self.publisher.publish("test_event", data)

        args, kwargs = self.mock_producer.produce.call_args
        assert args[0] == "default-topic"
        payload = json.loads(kwargs["value"])
        assert payload["event"] == "test_event"
        assert payload["data"] == data
        assert "callback" in kwargs

        self.mock_producer.flush.assert_called_once()

    def test_publish_sends_payload_to_custom_topic(self):
        data = {"foo": "bar"}
        self.publisher.publish("test_event", data, topic="custom-topic")

        args, kwargs = self.mock_producer.produce.call_args
        assert args[0] == "custom-topic"
        payload = json.loads(kwargs["value"])
        assert payload["event"] == "test_event"
        assert payload["data"] == data
        assert "callback" in kwargs

        self.mock_producer.flush.assert_called_once()

    def test_publish_logs_exception(self, caplog):
        self.mock_producer.produce.side_effect = Exception("Boom")
        with caplog.at_level("ERROR"):
            self.publisher.publish("event", {"x": 1})

        assert "Failed to publish Kafka event: Boom" in caplog.text

    def test_publish_user_created_calls_publish_with_correct_data(self):
        self.publisher.publish = MagicMock()
        user_id = ID()
        username = Username("alice")
        email = Email("a@b.com")
        self.publisher.publish_user_created(
            user_id=user_id, username=username, email=email
        )

        self.publisher.publish.assert_called_once_with(
            "user_created", {"id": user_id.value, "username": username.value, "email": email.value}
        )

    def test_publish_user_logged_in_calls_publish_with_correct_data(self):
        self.publisher.publish = MagicMock()
        user_id = ID()
        username = Username("alice")
        device = Device("mobile")
        session_id = ID()
        self.publisher.publish_user_logged_in(
            user_id=user_id, username=username, device=device, session_id=session_id
        )

        self.publisher.publish.assert_called_once_with(
            "user_logged_in",
            {"id": user_id.value, "username": username.value, "device": device.value, "session_id": session_id.value},
        )

    def test_publish_user_logged_out_calls_publish_with_correct_data(self):
        self.publisher.publish = MagicMock()
        user_id = ID()
        username = Username("alice")
        device = Device("mobile")
        session_id = ID()
        self.publisher.publish_user_logged_out(
            user_id=user_id, username=username, device=device, session_id=session_id
        )

        self.publisher.publish.assert_called_once_with(
            "user_logged_out",
            {"id": user_id.value, "username": username.value, "device": device.value, "session_id": session_id.value},
        )
