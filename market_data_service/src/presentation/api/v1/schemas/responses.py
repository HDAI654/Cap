from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class PriceLevelResponse(BaseModel):
    price: Decimal
    quantity: int


class OrderBookResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    instrument_id: str
    bids: list[PriceLevelResponse]
    asks: list[PriceLevelResponse]
    last_trade_price: Decimal | None
    last_trade_currency: str | None


class LastTradePriceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    instrument_id: str
    price: Decimal
    currency: str
