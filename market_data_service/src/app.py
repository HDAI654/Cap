from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.conf import Config
from src.infrastructure.cache.in_memory_market_data_reader import (
    InMemoryMarketDataReader,
)
from src.logging_config import setup_logging
from src.presentation.api.v1 import api_v1_router


def _build_reader():
    if Config.REDIS_ENABLED:
        from src.infrastructure.cache.redis_market_data_reader import (
            RedisMarketDataReader,
        )

        return RedisMarketDataReader(url=Config.REDIS_URL)
    return InMemoryMarketDataReader()


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    reader = app.state.market_data_reader
    if hasattr(reader, "connect"):
        await reader.connect()
    yield
    if hasattr(reader, "close"):
        await reader.close()


app = FastAPI(
    title="Market Data Service",
    description="Read-only market data (order book snapshots, last trade price).",
    version="1.0.0",
    lifespan=lifespan,
)

app.state.market_data_reader = _build_reader()
app.include_router(api_v1_router)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok", "service": Config.APP_NAME}
