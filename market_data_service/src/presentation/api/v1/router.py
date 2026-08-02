from fastapi import APIRouter

from src.presentation.api.v1.routers.market_data import router as market_data_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(market_data_router)
