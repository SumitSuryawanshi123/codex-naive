from fastapi import APIRouter, Depends

from app.api.dependencies import get_lookup_service
from app.models.lookups import Agent, Customer
from app.services.lookups import LookupService


router = APIRouter(tags=["lookups"])


@router.get("/customers", response_model=list[Customer])
def list_customers(service: LookupService = Depends(get_lookup_service)) -> list[dict]:
    return service.list_customers()


@router.get("/agents", response_model=list[Agent])
def list_agents(service: LookupService = Depends(get_lookup_service)) -> list[dict]:
    return service.list_agents()
