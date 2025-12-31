import pytest


@pytest.fixture(autouse=True)
def disable_kafka(mocker):
    mocker.patch(
        "auth_app.infrastructure.messaging.kafka_producer.Producer",
        autospec=True,
    )
