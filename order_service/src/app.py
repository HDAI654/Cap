from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.conf import Config
from src.database import async_session_maker, engine
from src.domain.ports.event_publisher import EventPublisher
from src.infrastructure.messaging.noop_event_publisher import NoOpEventPublisher
from src.infrastructure.messaging.rabbitmq_event_publisher import (
    RabbitMQEventPublisher,
)
from src.infrastructure.persistence.models import Base
from src.presentation.api.v1 import api_v1_router


def _build_event_publisher() -> EventPublisher:
    if Config.RABBITMQ_ENABLED:
        return RabbitMQEventPublisher(
            url=Config.RABBITMQ_URL,
            exchange_name=Config.RABBITMQ_ORDER_EVENTS_EXCHANGE,
            exchange_type=Config.RABBITMQ_EXCHANGE_TYPE,
        )
    return NoOpEventPublisher()


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    publisher = app.state.event_publisher
    if isinstance(publisher, RabbitMQEventPublisher):
        await publisher.connect()

    yield

    if isinstance(publisher, RabbitMQEventPublisher):
        await publisher.close()
    await engine.dispose()


app = FastAPI(
    title="Order Service",
    description="REST API for order ingress and lifecycle in the stock exchange.",
    version="1.0.0",
    lifespan=lifespan,
)

app.state.engine = engine
app.state.session_factory = async_session_maker
app.state.event_publisher = _build_event_publisher()
app.include_router(api_v1_router)
