import logging
from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, status

from src.application.get_last_trade_price import (
    GetLastTradePriceHandler,
    GetLastTradePriceQuery,
)
from src.application.get_order_book import GetOrderBookHandler, GetOrderBookQuery
from src.exceptions import (
    CacheConnectionError,
    CacheOperationError,
    InvalidInstrumentIdError,
    MarketDataNotFoundError,
)
from src.presentation.api.v1.schemas.responses import (
    LastTradePriceResponse,
    OrderBookResponse,
    PriceLevelResponse,
)
from src.presentation.dependencies import MarketDataReaderDep

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/market-data", tags=["market-data"])

InstrumentIdPath = Annotated[
    str,
    Path(..., min_length=36, max_length=36, description="Instrument UUID v4."),
]


@router.get(
    "/{instrument_id}/order-book",
    response_model=OrderBookResponse,
    status_code=status.HTTP_200_OK,
    summary="Get order book snapshot",
)
async def get_order_book(
    instrument_id: InstrumentIdPath,
    reader: MarketDataReaderDep,
) -> OrderBookResponse:
    handler = GetOrderBookHandler(reader)
    try:
        snapshot = await handler.handle(GetOrderBookQuery(instrument_id=instrument_id))
    except MarketDataNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except InvalidInstrumentIdError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        )
    except CacheConnectionError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        )
    except CacheOperationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        )
    except Exception:
        logger.exception("Unexpected error getting order book")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )

    return OrderBookResponse(
        instrument_id=snapshot.instrument_id,
        bids=[
            PriceLevelResponse(price=level.price, quantity=level.quantity)
            for level in snapshot.bids
        ],
        asks=[
            PriceLevelResponse(price=level.price, quantity=level.quantity)
            for level in snapshot.asks
        ],
        last_trade_price=snapshot.last_trade_price,
        last_trade_currency=snapshot.last_trade_currency,
    )


@router.get(
    "/{instrument_id}/last-trade-price",
    response_model=LastTradePriceResponse,
    status_code=status.HTTP_200_OK,
    summary="Get last trade price",
)
async def get_last_trade_price(
    instrument_id: InstrumentIdPath,
    reader: MarketDataReaderDep,
) -> LastTradePriceResponse:
    handler = GetLastTradePriceHandler(reader)
    try:
        ltp = await handler.handle(GetLastTradePriceQuery(instrument_id=instrument_id))
    except MarketDataNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except InvalidInstrumentIdError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        )
    except CacheConnectionError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        )
    except CacheOperationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        )
    except Exception:
        logger.exception("Unexpected error getting LTP")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )

    return LastTradePriceResponse(
        instrument_id=ltp.instrument_id,
        price=ltp.price,
        currency=ltp.currency,
    )
