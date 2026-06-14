from fastapi import APIRouter

from app.models.health import HealthResponse


router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> dict:
    return {"status": "ok", "service": "crm-tickets"}
