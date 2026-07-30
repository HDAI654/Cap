from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from src.exceptions import (
    ApplicationError,
    CashBalanceNotFoundError,
    CurrencyMismatchError,
    DomainError,
    HoldingNotFoundError,
    InvalidCurrencyError,
    InvalidInstrumentIdError,
    InvalidMoneyAmountError,
    InvalidQuantityError,
    InvalidTraderIdError,
    InvalidWalletIdError,
    WalletAlreadyExistsError,
    WalletNotActiveError,
    WalletNotFoundError,
)


def _error_body(detail: str) -> dict[str, str]:
    return {"detail": detail}


def register_exception_handlers(app: FastAPI) -> None:
    """Attach domain/application exception handlers to the FastAPI app."""

    @app.exception_handler(WalletNotFoundError)
    async def wallet_not_found(
        _request: Request,
        exc: WalletNotFoundError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=_error_body(str(exc) or "Wallet not found."),
        )

    @app.exception_handler(CashBalanceNotFoundError)
    async def cash_balance_not_found(
        _request: Request,
        exc: CashBalanceNotFoundError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=_error_body(str(exc) or "Cash balance not found."),
        )

    @app.exception_handler(HoldingNotFoundError)
    async def holding_not_found(
        _request: Request,
        exc: HoldingNotFoundError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=_error_body(str(exc) or "Holding not found."),
        )

    @app.exception_handler(WalletAlreadyExistsError)
    async def wallet_already_exists(
        _request: Request,
        exc: WalletAlreadyExistsError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=_error_body(str(exc) or "Wallet already exists."),
        )

    @app.exception_handler(WalletNotActiveError)
    async def wallet_not_active(
        _request: Request,
        exc: WalletNotActiveError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=_error_body(str(exc) or "Wallet is not active."),
        )

    @app.exception_handler(InvalidMoneyAmountError)
    async def invalid_money_amount(
        _request: Request,
        exc: InvalidMoneyAmountError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content=_error_body(str(exc) or "Invalid monetary amount."),
        )

    @app.exception_handler(InvalidQuantityError)
    async def invalid_quantity(
        _request: Request,
        exc: InvalidQuantityError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content=_error_body(str(exc) or "Invalid quantity."),
        )

    @app.exception_handler(InvalidCurrencyError)
    async def invalid_currency(
        _request: Request,
        exc: InvalidCurrencyError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content=_error_body(str(exc) or "Invalid currency."),
        )

    @app.exception_handler(CurrencyMismatchError)
    async def currency_mismatch(
        _request: Request,
        exc: CurrencyMismatchError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content=_error_body(str(exc) or "Currency mismatch."),
        )

    @app.exception_handler(InvalidWalletIdError)
    async def invalid_wallet_id(
        _request: Request,
        exc: InvalidWalletIdError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content=_error_body(str(exc) or "Invalid wallet id."),
        )

    @app.exception_handler(InvalidTraderIdError)
    async def invalid_trader_id(
        _request: Request,
        exc: InvalidTraderIdError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content=_error_body(str(exc) or "Invalid trader id."),
        )

    @app.exception_handler(InvalidInstrumentIdError)
    async def invalid_instrument_id(
        _request: Request,
        exc: InvalidInstrumentIdError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content=_error_body(str(exc) or "Invalid instrument id."),
        )

    @app.exception_handler(ApplicationError)
    async def application_error(
        _request: Request,
        exc: ApplicationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=_error_body(str(exc) or "Application error."),
        )

    @app.exception_handler(DomainError)
    async def domain_error(
        _request: Request,
        exc: DomainError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=_error_body(str(exc) or "Domain error."),
        )
