from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.conf import Config
from src.domain.connection_hub import ConnectionHub
from src.logging_config import setup_logging
from src.presentation.internal_router import router as internal_router
from src.presentation.websocket_router import router as websocket_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    yield


app = FastAPI(
    title="Notification Service",
    description=(
        "Real-time trader notifications via WebSocket. "
        "Receives pushes from Notification Dispatcher on the internal API."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.state.connection_hub = ConnectionHub()
app.include_router(internal_router)
app.include_router(websocket_router)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str | int]:
    hub: ConnectionHub = app.state.connection_hub
    return {
        "status": "ok",
        "service": Config.APP_NAME,
        "connected_traders": hub.connected_trader_count(),
    }
