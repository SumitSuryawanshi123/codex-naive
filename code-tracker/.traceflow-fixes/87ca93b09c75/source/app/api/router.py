from fastapi import APIRouter

from .routes import health, lookups, stats, tickets


api_router = APIRouter(prefix="/api")
api_router.include_router(health.router)
api_router.include_router(lookups.router)
api_router.include_router(stats.router)
api_router.include_router(tickets.router)
