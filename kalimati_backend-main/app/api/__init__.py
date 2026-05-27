# app/api/__init__.py
from fastapi import APIRouter
from .prices import router as prices_router
from .analytics import router as analytics_router

# Aggregate router — registered in main.py
api_router = APIRouter(prefix="/api/v1")
api_router.include_router(prices_router)
api_router.include_router(analytics_router)

__all__ = ["api_router"]
