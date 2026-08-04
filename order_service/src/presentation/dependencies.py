from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.conf import Config
from src.domain.ports.event_publisher import EventPublisher
from src.domain.ports.instrument_gateway import InstrumentGateway
from src.domain.ports.unit_of_work import UnitOfWork
from src.domain.ports.wallet_gateway import WalletGateway
from src.infrastructure.http_clients.http_instrument_gateway import (
    HttpInstrumentGateway,
)
from src.infrastructure.http_clients.http_wallet_gateway import HttpWalletGateway
from src.infrastructure.http_clients.noop_instrument_gateway import (
    NoOpInstrumentGateway,
)
from src.infrastructure.http_clients.noop_wallet_gateway import NoOpWalletGateway
from src.infrastructure.persistence.unit_of_work import SQLAlchemyUnitOfWork


def get_session_factory(request: Request) -> async_sessionmaker[AsyncSession]:
    return request.app.state.session_factory


def get_uow_factory(
    session_factory: Annotated[
        async_sessionmaker[AsyncSession],
        Depends(get_session_factory),
    ],
) -> Callable[[], UnitOfWork]:
    def factory() -> UnitOfWork:
        return SQLAlchemyUnitOfWork(session_factory)

    return factory


def get_event_publisher(request: Request) -> EventPublisher:
    return request.app.state.event_publisher


def get_wallet_gateway() -> WalletGateway:
    if Config.WALLET_INTEGRATION_ENABLED:
        return HttpWalletGateway(Config.WALLET_SERVICE_URL)
    return NoOpWalletGateway()


def get_instrument_gateway() -> InstrumentGateway:
    if Config.ADMIN_INTEGRATION_ENABLED:
        return HttpInstrumentGateway(Config.ADMIN_SERVICE_URL)
    return NoOpInstrumentGateway()


UoWFactory = Annotated[Callable[[], UnitOfWork], Depends(get_uow_factory)]
EventPublisherDep = Annotated[EventPublisher, Depends(get_event_publisher)]
WalletGatewayDep = Annotated[WalletGateway, Depends(get_wallet_gateway)]
InstrumentGatewayDep = Annotated[InstrumentGateway, Depends(get_instrument_gateway)]
