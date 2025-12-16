import pytest
import fakeredis


@pytest.fixture(autouse=True)
def disable_kafka(mocker):
    mocker.patch(
        "accounts.services.kafka_producer.Producer",
        autospec=True,
    )

@pytest.fixture(autouse=True)
def patch_redis(mocker):
    """
    Patch redis client used by SessionManager for all tests.
    """
    fake = fakeredis.FakeStrictRedis()
    mocker.patch(
        "accounts.services.session_service.redis_client",
        fake,
    )
    return fake
