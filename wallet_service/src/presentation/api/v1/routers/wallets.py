import logging
from typing import Annotated
from fastapi import APIRouter, Path, Response, status, HTTPException

# handlers & commands
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

# Exceptions
from src.exceptions import (
    DatabaseConnectionError,
    DatabaseOperationError,
    DatabaseTimeoutError,
    WalletNotFoundError,
    WalletAlreadyExistsError,
    InvalidTraderIdError,
    InvalidWalletIdError,
    WalletNotActiveError,
    InvalidCurrencyError,
    InvalidMoneyAmountError,
    CurrencyMismatchError,
    CashBalanceNotFoundError,
    InvalidInstrumentIdError,
    InvalidQuantityError,
    HoldingNotFoundError,
)

logger = logging.getLogger(__name__)

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
    """Create a new wallet for a trader."""
    logger.info("Creating wallet: trader_id=%s", body.trader_id)
    handler = CreateWalletHandler(uow_factory())
    try:
        result = await handler.handle(
            CreateWalletCommand(trader_id=body.trader_id),
        )
    except WalletAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc) or "Wallet already exists.",
        )
    except InvalidTraderIdError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc) or "Invalid trader id.",
        )
    except (DatabaseConnectionError, DatabaseTimeoutError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc) or "Database temporarily unavailable.",
        )
    except DatabaseOperationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc) or "Database operation failed.",
        )
    except Exception:
        logger.exception("Unexpected error while creating wallet")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )

    logger.info("Wallet created: wallet_id=%s", result.wallet_id)
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
    logger.info("Retrieving wallet: wallet_id=%s", wallet_id)
    handler = GetWalletHandler(uow_factory())
    try:
        dto = await handler.handle(GetWalletQuery(wallet_id=wallet_id))
    except WalletNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc) or "Wallet not found.",
        )
    except InvalidWalletIdError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc) or "Invalid wallet id.",
        )
    except (DatabaseConnectionError, DatabaseTimeoutError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc) or "Database temporarily unavailable.",
        )
    except DatabaseOperationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc) or "Database operation failed.",
        )
    except Exception:
        logger.exception("Unexpected error while retrieving wallet")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )

    logger.info("Wallet retrieved: wallet_id=%s, status=%s", dto.wallet_id, dto.status)
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
    logger.info("Locking wallet: wallet_id=%s", wallet_id)
    handler = LockWalletHandler(uow_factory())
    try:
        await handler.handle(LockWalletCommand(wallet_id=wallet_id))
    except WalletNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc) or "Wallet not found.",
        )
    except InvalidWalletIdError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc) or "Invalid wallet id.",
        )
    except (DatabaseConnectionError, DatabaseTimeoutError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc) or "Database temporarily unavailable.",
        )
    except DatabaseOperationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc) or "Database operation failed.",
        )
    except Exception:
        logger.exception("Unexpected error while locking wallet")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )

    logger.info("Wallet locked: wallet_id=%s", wallet_id)
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
    logger.info("Activating wallet: wallet_id=%s", wallet_id)
    handler = ActivateWalletHandler(uow_factory())
    try:
        await handler.handle(ActivateWalletCommand(wallet_id=wallet_id))
    except WalletNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc) or "Wallet not found.",
        )
    except InvalidWalletIdError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc) or "Invalid wallet id.",
        )
    except (DatabaseConnectionError, DatabaseTimeoutError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc) or "Database temporarily unavailable.",
        )
    except DatabaseOperationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc) or "Database operation failed.",
        )
    except Exception:
        logger.exception("Unexpected error while activating wallet")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )

    logger.info("Wallet activated: wallet_id=%s", wallet_id)
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
    logger.info("Closing wallet: wallet_id=%s", wallet_id)
    handler = CloseWalletHandler(uow_factory())
    try:
        await handler.handle(CloseWalletCommand(wallet_id=wallet_id))
    except WalletNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc) or "Wallet not found.",
        )
    except InvalidWalletIdError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc) or "Invalid wallet id.",
        )
    except (DatabaseConnectionError, DatabaseTimeoutError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc) or "Database temporarily unavailable.",
        )
    except DatabaseOperationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc) or "Database operation failed.",
        )
    except Exception:
        logger.exception("Unexpected error while closing wallet")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )

    logger.info("Wallet closed: wallet_id=%s", wallet_id)
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
    logger.info(
        "Depositing cash: wallet_id=%s, amount=%s, currency=%s",
        wallet_id,
        body.amount,
        body.currency,
    )
    handler = DepositCashHandler(uow_factory())
    try:
        await handler.handle(
            DepositCashCommand(
                wallet_id=wallet_id,
                amount=body.amount,
                currency=body.currency,
            ),
        )
    except WalletNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc) or "Wallet not found.",
        )
    except WalletNotActiveError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc) or "Wallet is not active.",
        )
    except (
        InvalidWalletIdError,
        InvalidCurrencyError,
        InvalidMoneyAmountError,
        CurrencyMismatchError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc) or "Invalid request data.",
        )
    except (DatabaseConnectionError, DatabaseTimeoutError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc) or "Database temporarily unavailable.",
        )
    except DatabaseOperationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc) or "Database operation failed.",
        )
    except Exception:
        logger.exception("Unexpected error while depositing cash")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )

    logger.info(
        "Cash deposited: wallet_id=%s, amount=%s, currency=%s",
        wallet_id,
        body.amount,
        body.currency,
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
    logger.info(
        "Withdrawing cash: wallet_id=%s, amount=%s, currency=%s",
        wallet_id,
        body.amount,
        body.currency,
    )
    handler = WithdrawCashHandler(uow_factory())
    try:
        await handler.handle(
            WithdrawCashCommand(
                wallet_id=wallet_id,
                amount=body.amount,
                currency=body.currency,
            ),
        )
    except (WalletNotFoundError, CashBalanceNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc) or "Wallet or cash balance not found.",
        )
    except WalletNotActiveError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc) or "Wallet is not active.",
        )
    except (
        InvalidWalletIdError,
        InvalidCurrencyError,
        InvalidMoneyAmountError,
        CurrencyMismatchError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc) or "Invalid request data.",
        )
    except (DatabaseConnectionError, DatabaseTimeoutError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc) or "Database temporarily unavailable.",
        )
    except DatabaseOperationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc) or "Database operation failed.",
        )
    except Exception:
        logger.exception("Unexpected error while withdrawing cash")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )

    logger.info(
        "Cash withdrawn: wallet_id=%s, amount=%s, currency=%s",
        wallet_id,
        body.amount,
        body.currency,
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
    logger.info(
        "Reserving cash: wallet_id=%s, amount=%s, currency=%s",
        wallet_id,
        body.amount,
        body.currency,
    )
    handler = ReserveCashHandler(uow_factory())
    try:
        await handler.handle(
            ReserveCashCommand(
                wallet_id=wallet_id,
                amount=body.amount,
                currency=body.currency,
            ),
        )
    except (WalletNotFoundError, CashBalanceNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc) or "Wallet or cash balance not found.",
        )
    except WalletNotActiveError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc) or "Wallet is not active.",
        )
    except (
        InvalidWalletIdError,
        InvalidCurrencyError,
        InvalidMoneyAmountError,
        CurrencyMismatchError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc) or "Invalid request data.",
        )
    except (DatabaseConnectionError, DatabaseTimeoutError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc) or "Database temporarily unavailable.",
        )
    except DatabaseOperationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc) or "Database operation failed.",
        )
    except Exception:
        logger.exception("Unexpected error while reserving cash")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )

    logger.info(
        "Cash reserved: wallet_id=%s, amount=%s, currency=%s",
        wallet_id,
        body.amount,
        body.currency,
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
    logger.info(
        "Releasing reserved cash: wallet_id=%s, amount=%s, currency=%s",
        wallet_id,
        body.amount,
        body.currency,
    )
    handler = ReleaseCashHandler(uow_factory())
    try:
        await handler.handle(
            ReleaseCashCommand(
                wallet_id=wallet_id,
                amount=body.amount,
                currency=body.currency,
            ),
        )
    except (WalletNotFoundError, CashBalanceNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc) or "Wallet or cash balance not found.",
        )
    except WalletNotActiveError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc) or "Wallet is not active.",
        )
    except (
        InvalidWalletIdError,
        InvalidCurrencyError,
        InvalidMoneyAmountError,
        CurrencyMismatchError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc) or "Invalid request data.",
        )
    except (DatabaseConnectionError, DatabaseTimeoutError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc) or "Database temporarily unavailable.",
        )
    except DatabaseOperationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc) or "Database operation failed.",
        )
    except Exception:
        logger.exception("Unexpected error while releasing cash")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )

    logger.info(
        "Reserved cash released: wallet_id=%s, amount=%s, currency=%s",
        wallet_id,
        body.amount,
        body.currency,
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
    logger.info(
        "Consuming reserved cash: wallet_id=%s, amount=%s, currency=%s",
        wallet_id,
        body.amount,
        body.currency,
    )
    handler = ConsumeReservedCashHandler(uow_factory())
    try:
        await handler.handle(
            ConsumeReservedCashCommand(
                wallet_id=wallet_id,
                amount=body.amount,
                currency=body.currency,
            ),
        )
    except (WalletNotFoundError, CashBalanceNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc) or "Wallet or cash balance not found.",
        )
    except WalletNotActiveError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc) or "Wallet is not active.",
        )
    except (
        InvalidWalletIdError,
        InvalidCurrencyError,
        InvalidMoneyAmountError,
        CurrencyMismatchError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc) or "Invalid request data.",
        )
    except (DatabaseConnectionError, DatabaseTimeoutError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc) or "Database temporarily unavailable.",
        )
    except DatabaseOperationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc) or "Database operation failed.",
        )
    except Exception:
        logger.exception("Unexpected error while consuming reserved cash")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )

    logger.info(
        "Reserved cash consumed: wallet_id=%s, amount=%s, currency=%s",
        wallet_id,
        body.amount,
        body.currency,
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
    logger.info(
        "Adding holding: wallet_id=%s, instrument_id=%s, quantity=%s, avg_cost=%s %s",
        wallet_id,
        body.instrument_id,
        body.quantity,
        body.average_cost,
        body.average_cost_currency,
    )
    handler = AddHoldingHandler(uow_factory())
    try:
        await handler.handle(
            AddHoldingCommand(
                wallet_id=wallet_id,
                instrument_id=body.instrument_id,
                quantity=body.quantity,
                average_cost=body.average_cost,
                average_cost_currency=body.average_cost_currency,
            ),
        )
    except WalletNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc) or "Wallet not found.",
        )
    except WalletNotActiveError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc) or "Wallet is not active.",
        )
    except (
        InvalidWalletIdError,
        InvalidInstrumentIdError,
        InvalidQuantityError,
        InvalidCurrencyError,
        InvalidMoneyAmountError,
        CurrencyMismatchError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc) or "Invalid request data.",
        )
    except (DatabaseConnectionError, DatabaseTimeoutError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc) or "Database temporarily unavailable.",
        )
    except DatabaseOperationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc) or "Database operation failed.",
        )
    except Exception:
        logger.exception("Unexpected error while adding holding")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )

    logger.info(
        "Holding added: wallet_id=%s, instrument_id=%s, quantity=%s",
        wallet_id,
        body.instrument_id,
        body.quantity,
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
    logger.info(
        "Removing holding: wallet_id=%s, instrument_id=%s, quantity=%s",
        wallet_id,
        body.instrument_id,
        body.quantity,
    )
    handler = RemoveHoldingHandler(uow_factory())
    try:
        await handler.handle(
            RemoveHoldingCommand(
                wallet_id=wallet_id,
                instrument_id=body.instrument_id,
                quantity=body.quantity,
            ),
        )
    except (WalletNotFoundError, HoldingNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc) or "Wallet or holding not found.",
        )
    except WalletNotActiveError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc) or "Wallet is not active.",
        )
    except (
        InvalidWalletIdError,
        InvalidInstrumentIdError,
        InvalidQuantityError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc) or "Invalid request data.",
        )
    except (DatabaseConnectionError, DatabaseTimeoutError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc) or "Database temporarily unavailable.",
        )
    except DatabaseOperationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc) or "Database operation failed.",
        )
    except Exception:
        logger.exception("Unexpected error while removing holding")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )

    logger.info(
        "Holding removed: wallet_id=%s, instrument_id=%s, quantity=%s",
        wallet_id,
        body.instrument_id,
        body.quantity,
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
    logger.info(
        "Reserving holding: wallet_id=%s, instrument_id=%s, quantity=%s",
        wallet_id,
        body.instrument_id,
        body.quantity,
    )
    handler = ReserveHoldingHandler(uow_factory())
    try:
        await handler.handle(
            ReserveHoldingCommand(
                wallet_id=wallet_id,
                instrument_id=body.instrument_id,
                quantity=body.quantity,
            ),
        )
    except (WalletNotFoundError, HoldingNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc) or "Wallet or holding not found.",
        )
    except WalletNotActiveError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc) or "Wallet is not active.",
        )
    except (
        InvalidWalletIdError,
        InvalidInstrumentIdError,
        InvalidQuantityError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc) or "Invalid request data.",
        )
    except (DatabaseConnectionError, DatabaseTimeoutError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc) or "Database temporarily unavailable.",
        )
    except DatabaseOperationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc) or "Database operation failed.",
        )
    except Exception:
        logger.exception("Unexpected error while reserving holding")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )

    logger.info(
        "Holding reserved: wallet_id=%s, instrument_id=%s, quantity=%s",
        wallet_id,
        body.instrument_id,
        body.quantity,
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
    logger.info(
        "Releasing holding: wallet_id=%s, instrument_id=%s, quantity=%s",
        wallet_id,
        body.instrument_id,
        body.quantity,
    )
    handler = ReleaseHoldingHandler(uow_factory())
    try:
        await handler.handle(
            ReleaseHoldingCommand(
                wallet_id=wallet_id,
                instrument_id=body.instrument_id,
                quantity=body.quantity,
            ),
        )
    except (WalletNotFoundError, HoldingNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc) or "Wallet or holding not found.",
        )
    except WalletNotActiveError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc) or "Wallet is not active.",
        )
    except (
        InvalidWalletIdError,
        InvalidInstrumentIdError,
        InvalidQuantityError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc) or "Invalid request data.",
        )
    except (DatabaseConnectionError, DatabaseTimeoutError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc) or "Database temporarily unavailable.",
        )
    except DatabaseOperationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc) or "Database operation failed.",
        )
    except Exception:
        logger.exception("Unexpected error while releasing holding")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )

    logger.info(
        "Holding released: wallet_id=%s, instrument_id=%s, quantity=%s",
        wallet_id,
        body.instrument_id,
        body.quantity,
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
    logger.info(
        "Consuming reserved holding: wallet_id=%s, instrument_id=%s, quantity=%s",
        wallet_id,
        body.instrument_id,
        body.quantity,
    )
    handler = ConsumeReservedHoldingHandler(uow_factory())
    try:
        await handler.handle(
            ConsumeReservedHoldingCommand(
                wallet_id=wallet_id,
                instrument_id=body.instrument_id,
                quantity=body.quantity,
            ),
        )
    except (WalletNotFoundError, HoldingNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc) or "Wallet or holding not found.",
        )
    except WalletNotActiveError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc) or "Wallet is not active.",
        )
    except (
        InvalidWalletIdError,
        InvalidInstrumentIdError,
        InvalidQuantityError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc) or "Invalid request data.",
        )
    except (DatabaseConnectionError, DatabaseTimeoutError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc) or "Database temporarily unavailable.",
        )
    except DatabaseOperationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc) or "Database operation failed.",
        )
    except Exception:
        logger.exception("Unexpected error while consuming reserved holding")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )

    logger.info(
        "Reserved holding consumed: wallet_id=%s, instrument_id=%s, quantity=%s",
        wallet_id,
        body.instrument_id,
        body.quantity,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
