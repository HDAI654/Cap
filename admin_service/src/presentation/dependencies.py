from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.domain.ports.unit_of_work import UnitOfWork
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


UoWFactory = Annotated[Callable[[], UnitOfWork], Depends(get_uow_factory)]
