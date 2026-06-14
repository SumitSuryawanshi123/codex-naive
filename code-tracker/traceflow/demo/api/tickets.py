from __future__ import annotations

from fastapi import APIRouter, Response, status

from ..models import TicketCreate, TicketUpdate
from ..services.tickets import TicketService
from ...tracing import trace_step


router = APIRouter(tags=["tickets"])
service = TicketService()


@router.post("/tickets", status_code=status.HTTP_201_CREATED)
async def create_ticket(ticket: TicketCreate) -> dict:
    with trace_step("route handler create_ticket", kind="route", detail="POST /api/tickets"):
        result = service.create_ticket(ticket)
    with trace_step("serialize response", kind="route", detail="Ticket JSON body"):
        return result


@router.get("/tickets")
async def list_tickets() -> list[dict]:
    with trace_step("route handler list_tickets", kind="route", detail="GET /api/tickets"):
        result = service.list_tickets()
    with trace_step("serialize response", kind="route", detail="Ticket list JSON body"):
        return result


@router.get("/tickets/{ticket_id}")
async def get_ticket(ticket_id: int) -> dict:
    with trace_step("route handler get_ticket", kind="route", detail="GET /api/tickets/{ticket_id}"):
        result = service.get_ticket(ticket_id)
    with trace_step("serialize response", kind="route", detail="Ticket JSON body"):
        return result


@router.patch("/tickets/{ticket_id}")
async def update_ticket(ticket_id: int, update: TicketUpdate) -> dict:
    with trace_step("route handler update_ticket", kind="route", detail="PATCH /api/tickets/{ticket_id}"):
        result = service.update_ticket(ticket_id, update)
    with trace_step("serialize response", kind="route", detail="Ticket JSON body"):
        return result


@router.delete("/tickets/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ticket(ticket_id: int) -> Response:
    with trace_step("route handler delete_ticket", kind="route", detail="DELETE /api/tickets/{ticket_id}"):
        service.delete_ticket(ticket_id)
    with trace_step("serialize response", kind="route", detail="No content"):
        return Response(status_code=status.HTTP_204_NO_CONTENT)
