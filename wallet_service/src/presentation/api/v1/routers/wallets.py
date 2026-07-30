from typing import Annotated
from fastapi import APIRouter, Path, Response, status
from src.application.activate_wallet import (
    ActivateWalletCommand,
    ActivateWalletHandler,
)
from src.application.add_holding import AddHoldingCommand, AddHoldingHandler
from src.application.close_wallet import CloseWalletCommand, CloseWalletHandler
from src.application.consume_reserved_cash import (
    ConsumeReservedCashCommand,
    ConsumeReservedCashHandler,
)
from src.application.consume_reserved_holding import (
    ConsumeReservedHoldingCommand,
    ConsumeReservedHoldingHandler,
)
from src.application.create_wallet import (
    CreateWalletCommand,
    CreateWalletHandler,
)
from src.application.deposit_cash import DepositCashCommand, DepositCashHandler
from src.application.get_wallet import GetWalletHandler, GetWalletQuery
from src.application.lock_wallet import LockWalletCommand, LockWalletHandler
from src.application.release_cash import ReleaseCashCommand, ReleaseCashHandler
from src.application.release_holding import (
    ReleaseHoldingCommand,
    ReleaseHoldingHandler,
)
from src.application.remove_holding import (
    RemoveHoldingCommand,
    RemoveHoldingHandler,
)
from src.application.reserve_cash import ReserveCashCommand, ReserveCashHandler
from src.application.reserve_holding import (
    ReserveHoldingCommand,
    ReserveHoldingHandler,
)
from src.application.withdraw_cash import (
    WithdrawCashCommand,
    WithdrawCashHandler,
)
from src.presentation.dependencies import UoWFactory
from src.presentation.api.v1.schemas.requests import (
    AddHoldingRequest,
    CreateWalletRequest,
    HoldingQuantityRequest,
    MoneyRequest,
)
from src.presentation.api.v1.schemas.responses import (
    CreateWalletResponse,
    WalletResponse,
)

router = APIRouter(prefix="/wallets", tags=["wallets"])

WalletIdPath = Annotated[
    str,
    Path(
        ...,
        min_length=36,
        max_length=36,
        description="Wallet UUID v4 identifier.",
    ),
]


# ---------------------------------------------------------------------------
# Wallet lifecycle
# ---------------------------------------------------------------------------


@router.post(
    "",
    response_model=CreateWalletResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a wallet",
)
async def create_wallet(
    body: CreateWalletRequest,
    uow_factory: UoWFactory,
) -> CreateWalletResponse:
    """Create a new wallet for a trader.

    Returns 409 if a wallet already exists for the trader.
    """
    handler = CreateWalletHandler(uow_factory())
    result = await handler.handle(
        CreateWalletCommand(trader_id=body.trader_id),
    )
    return CreateWalletResponse(wallet_id=result.wallet_id)


@router.get(
    "/{wallet_id}",
    response_model=WalletResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a wallet",
)
async def get_wallet(
    wallet_id: WalletIdPath,
    uow_factory: UoWFactory,
) -> WalletResponse:
    """Retrieve a wallet by identifier, including cash balances and holdings."""
    handler = GetWalletHandler(uow_factory())
    dto = await handler.handle(GetWalletQuery(wallet_id=wallet_id))
    return WalletResponse(
        wallet_id=dto.wallet_id,
        trader_id=dto.trader_id,
        status=dto.status,
        cash_balances=[
            {
                "currency": b.currency,
                "available": b.available,
                "reserved": b.reserved,
            }
            for b in dto.cash_balances
        ],
        holdings=[
            {
                "instrument_id": h.instrument_id,
                "available": h.available,
                "reserved": h.reserved,
                "average_cost": h.average_cost,
                "average_cost_currency": h.average_cost_currency,
            }
            for h in dto.holdings
        ],
    )


@router.post(
    "/{wallet_id}/lock",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Lock a wallet",
)
async def lock_wallet(
    wallet_id: WalletIdPath,
    uow_factory: UoWFactory,
) -> Response:
    """Transition the wallet to LOCKED status."""
    handler = LockWalletHandler(uow_factory())
    await handler.handle(LockWalletCommand(wallet_id=wallet_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{wallet_id}/activate",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Activate a wallet",
)
async def activate_wallet(
    wallet_id: WalletIdPath,
    uow_factory: UoWFactory,
) -> Response:
    """Transition the wallet to ACTIVE status."""
    handler = ActivateWalletHandler(uow_factory())
    await handler.handle(ActivateWalletCommand(wallet_id=wallet_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{wallet_id}/close",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Close a wallet",
)
async def close_wallet(
    wallet_id: WalletIdPath,
    uow_factory: UoWFactory,
) -> Response:
    """Transition the wallet to CLOSED status."""
    handler = CloseWalletHandler(uow_factory())
    await handler.handle(CloseWalletCommand(wallet_id=wallet_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Cash operations
# ---------------------------------------------------------------------------


@router.post(
    "/{wallet_id}/deposits",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deposit cash",
)
async def deposit_cash(
    wallet_id: WalletIdPath,
    body: MoneyRequest,
    uow_factory: UoWFactory,
) -> Response:
    """Deposit available cash into the wallet."""
    handler = DepositCashHandler(uow_factory())
    await handler.handle(
        DepositCashCommand(
            wallet_id=wallet_id,
            amount=body.amount,
            currency=body.currency,
        ),
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{wallet_id}/withdrawals",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Withdraw cash",
)
async def withdraw_cash(
    wallet_id: WalletIdPath,
    body: MoneyRequest,
    uow_factory: UoWFactory,
) -> Response:
    """Withdraw available cash from the wallet."""
    handler = WithdrawCashHandler(uow_factory())
    await handler.handle(
        WithdrawCashCommand(
            wallet_id=wallet_id,
            amount=body.amount,
            currency=body.currency,
        ),
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{wallet_id}/cash-reservations",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Reserve cash",
)
async def reserve_cash(
    wallet_id: WalletIdPath,
    body: MoneyRequest,
    uow_factory: UoWFactory,
) -> Response:
    """Reserve available cash for an order."""
    handler = ReserveCashHandler(uow_factory())
    await handler.handle(
        ReserveCashCommand(
            wallet_id=wallet_id,
            amount=body.amount,
            currency=body.currency,
        ),
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{wallet_id}/cash-releases",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Release reserved cash",
)
async def release_cash(
    wallet_id: WalletIdPath,
    body: MoneyRequest,
    uow_factory: UoWFactory,
) -> Response:
    """Release previously reserved cash back to available."""
    handler = ReleaseCashHandler(uow_factory())
    await handler.handle(
        ReleaseCashCommand(
            wallet_id=wallet_id,
            amount=body.amount,
            currency=body.currency,
        ),
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{wallet_id}/cash-settlements",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Consume reserved cash",
)
async def consume_reserved_cash(
    wallet_id: WalletIdPath,
    body: MoneyRequest,
    uow_factory: UoWFactory,
) -> Response:
    """Permanently consume reserved cash after settlement."""
    handler = ConsumeReservedCashHandler(uow_factory())
    await handler.handle(
        ConsumeReservedCashCommand(
            wallet_id=wallet_id,
            amount=body.amount,
            currency=body.currency,
        ),
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Holding operations
# ---------------------------------------------------------------------------


@router.post(
    "/{wallet_id}/holdings",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Add holding shares",
)
async def add_holding(
    wallet_id: WalletIdPath,
    body: AddHoldingRequest,
    uow_factory: UoWFactory,
) -> Response:
    """Add shares to a holding (creates the holding if needed)."""
    handler = AddHoldingHandler(uow_factory())
    await handler.handle(
        AddHoldingCommand(
            wallet_id=wallet_id,
            instrument_id=body.instrument_id,
            quantity=body.quantity,
            average_cost=body.average_cost,
            average_cost_currency=body.average_cost_currency,
        ),
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{wallet_id}/holding-removals",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove holding shares",
)
async def remove_holding(
    wallet_id: WalletIdPath,
    body: HoldingQuantityRequest,
    uow_factory: UoWFactory,
) -> Response:
    """Remove available shares from a holding."""
    handler = RemoveHoldingHandler(uow_factory())
    await handler.handle(
        RemoveHoldingCommand(
            wallet_id=wallet_id,
            instrument_id=body.instrument_id,
            quantity=body.quantity,
        ),
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{wallet_id}/holding-reservations",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Reserve holding shares",
)
async def reserve_holding(
    wallet_id: WalletIdPath,
    body: HoldingQuantityRequest,
    uow_factory: UoWFactory,
) -> Response:
    """Reserve available shares for an order."""
    handler = ReserveHoldingHandler(uow_factory())
    await handler.handle(
        ReserveHoldingCommand(
            wallet_id=wallet_id,
            instrument_id=body.instrument_id,
            quantity=body.quantity,
        ),
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{wallet_id}/holding-releases",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Release reserved holding shares",
)
async def release_holding(
    wallet_id: WalletIdPath,
    body: HoldingQuantityRequest,
    uow_factory: UoWFactory,
) -> Response:
    """Release previously reserved shares back to available."""
    handler = ReleaseHoldingHandler(uow_factory())
    await handler.handle(
        ReleaseHoldingCommand(
            wallet_id=wallet_id,
            instrument_id=body.instrument_id,
            quantity=body.quantity,
        ),
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{wallet_id}/holding-settlements",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Consume reserved holding shares",
)
async def consume_reserved_holding(
    wallet_id: WalletIdPath,
    body: HoldingQuantityRequest,
    uow_factory: UoWFactory,
) -> Response:
    """Permanently consume reserved shares after settlement."""
    handler = ConsumeReservedHoldingHandler(uow_factory())
    await handler.handle(
        ConsumeReservedHoldingCommand(
            wallet_id=wallet_id,
            instrument_id=body.instrument_id,
            quantity=body.quantity,
        ),
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
