"""API v1 root router."""

from fastapi import APIRouter

from src.presentation.api.v1.routers.orders import router as orders_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(orders_router)
