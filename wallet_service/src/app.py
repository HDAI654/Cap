from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.database import async_session_maker, engine
from src.infrastructure.persistence.models import Base
from src.presentation.api.v1 import api_v1_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="Wallet Service",
    description="REST API for trader wallet management in the stock exchange.",
    version="1.0.0",
    lifespan=lifespan,
)

app.state.engine = engine
app.state.session_factory = async_session_maker
app.include_router(api_v1_router)
