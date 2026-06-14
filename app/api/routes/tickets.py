from fastapi import APIRouter, Depends, Query, Response, status

from app.api.dependencies import get_ticket_service
from app.models.tickets import (
    Comment,
    CommentCreate,
    ExportInvoiceRequest,
    TicketCreate,
    TicketDetail,
    TicketFilters,
    TicketPriority,
    TicketStatus,
    TicketSummary,
    TicketUpdate,
)
from app.services.tickets import TicketService


router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.get("", response_model=list[TicketSummary])
def list_tickets(
    status_filter: TicketStatus | None = Query(default=None, alias="status"),
    priority: TicketPriority | None = None,
    agent_id: int | None = None,
    q: str | None = Query(default=None, max_length=100),
    service: TicketService = Depends(get_ticket_service),
) -> list[dict]:
    filters = TicketFilters(status=status_filter, priority=priority, agent_id=agent_id, q=q)
    return service.list_tickets(filters)


@router.get("/{ticket_id}", response_model=TicketDetail)
def get_ticket(ticket_id: int, service: TicketService = Depends(get_ticket_service)) -> dict:
    return service.get_ticket(ticket_id)


@router.post("", response_model=TicketDetail, status_code=status.HTTP_201_CREATED)
def create_ticket(ticket: TicketCreate, service: TicketService = Depends(get_ticket_service)) -> dict:
    return service.create_ticket(ticket)


@router.patch("/{ticket_id}", response_model=TicketDetail)
def update_ticket(
    ticket_id: int,
    update: TicketUpdate,
    service: TicketService = Depends(get_ticket_service),
) -> dict:
    return service.update_ticket(ticket_id, update)


@router.delete("/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ticket(ticket_id: int, service: TicketService = Depends(get_ticket_service)) -> Response:
    service.delete_ticket(ticket_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{ticket_id}/comments", response_model=Comment, status_code=status.HTTP_201_CREATED)
def add_comment(
    ticket_id: int,
    comment: CommentCreate,
    service: TicketService = Depends(get_ticket_service),
) -> dict:
    return service.add_comment(ticket_id, comment)


@router.post("/{ticket_id}/export-invoice")
def export_invoice(
    ticket_id: int,
    payload: ExportInvoiceRequest,
    scenario: str | None = Query(
        default=None,
        description="Demo failure mode: missing_config, billing_timeout. Default fails on auth or missing billing profile.",
    ),
    service: TicketService = Depends(get_ticket_service),
) -> dict:
    """
    Demo endpoint with intentional bugs for DebugOS / TraceFlow Fix This testing.

    Try ticket #1 (Billing) with:
    - No body -> 403 missing bearer token (SECURITY)
    - authorization without export:admin scope -> 403 missing scope (SECURITY)
    - authorization bearer export:admin token -> KeyError billing_profile (DATA)
    - ?scenario=missing_config + valid auth -> missing BILLING_EXPORT_SECRET (CONFIGURATION)
    - ?scenario=billing_timeout + valid auth -> Stripe timeout (EXTERNAL_SERVICE)
    """
    return service.export_invoice(ticket_id, payload.authorization, scenario)
