from typing import Annotated

from fastapi import Depends, Request

from src.domain.ports.market_data_reader import MarketDataReader


def get_market_data_reader(request: Request) -> MarketDataReader:
    return request.app.state.market_data_reader


MarketDataReaderDep = Annotated[MarketDataReader, Depends(get_market_data_reader)]
