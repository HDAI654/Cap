import pytest


@pytest.fixture(autouse=True)
def disable_kafka(mocker):
    mocker.patch(
        "accounts.services.kafka_producer.Producer",
        autospec=True,
    )
