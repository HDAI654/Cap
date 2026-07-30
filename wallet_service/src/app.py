from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool
from src.infrastructure.persistence.models import Base
from src.presentation.api.v1.router import api_v1_router
from src.presentation.exception_handlers import register_exception_handlers


def create_app(
    database_url: str = "sqlite+aiosqlite:///:memory:",
    *,
    echo_sql: bool = False,
) -> FastAPI:
    """Build and configure the FastAPI application."""
    engine_kwargs: dict = {"echo": echo_sql}
    if database_url.startswith("sqlite"):
        engine_kwargs["connect_args"] = {"check_same_thread": False}
        if ":memory:" in database_url:
            engine_kwargs["poolclass"] = StaticPool

    engine = create_async_engine(database_url, **engine_kwargs)
    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
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
    app.state.session_factory = session_factory
    register_exception_handlers(app)
    app.include_router(api_v1_router)
    return app
