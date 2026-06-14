from fastapi import APIRouter, Depends

from app.api.dependencies import get_stats_service
from app.models.stats import StatsResponse
from app.services.stats import StatsService


router = APIRouter(tags=["stats"])


@router.get("/stats", response_model=StatsResponse)
def dashboard_stats(service: StatsService = Depends(get_stats_service)) -> dict:
    return service.dashboard()
