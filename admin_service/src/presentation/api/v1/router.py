from fastapi import APIRouter

from src.presentation.api.v1.routers.instruments import router as instruments_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(instruments_router)
