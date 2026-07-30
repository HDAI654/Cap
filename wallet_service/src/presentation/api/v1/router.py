"""API v1 root router."""

from fastapi import APIRouter

from src.presentation.api.v1.routers.wallets import router as wallets_router

api_v1_router = APIRouter(prefix="/api/v1/wallets")
api_v1_router.include_router(wallets_router)
