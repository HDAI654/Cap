import pytest
import fakeredis


@pytest.fixture(autouse=True)
def disable_kafka(mocker):
    mocker.patch(
        "auth_app.infrastructure.messaging.kafka_producer.Producer",
        autospec=True,
    )


@pytest.fixture(autouse=True)
def patch_redis(mocker):
    fake = fakeredis.FakeStrictRedis()
    mocker.patch(
        "auth_app.infrastructure.cache.redis_client._redis_client",
        fake,
    )
    return fake
