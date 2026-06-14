from __future__ import annotations

from fastapi import HTTPException

from ..db import connect_ticket_store
from ..models import TicketCreate, TicketUpdate, model_payload
from ..repositories.tickets import TicketRepository
from ...tracing import traced, trace_step


class TicketService:
    @traced("TicketService.create_ticket", kind="service")
    def create_ticket(self, ticket: TicketCreate) -> dict:
        with trace_step("validate ticket payload", kind="validation", detail="Required customer and subject fields"):
            payload = model_payload(ticket)

        with connect_ticket_store() as store:
            repository = TicketRepository(store)
            created = repository.create(payload)
            return repository.get(created["id"]) or created

    @traced("TicketService.list_tickets", kind="service")
    def list_tickets(self) -> list[dict]:
        with connect_ticket_store() as store:
            repository = TicketRepository(store)
            return repository.list()

    @traced("TicketService.get_ticket", kind="service")
    def get_ticket(self, ticket_id: int) -> dict:
        with connect_ticket_store() as store:
            repository = TicketRepository(store)
            ticket = repository.get(ticket_id)
        if ticket is None:
            raise HTTPException(status_code=404, detail="Ticket not found")
        return ticket

    @traced("TicketService.update_ticket", kind="service")
    def update_ticket(self, ticket_id: int, update: TicketUpdate) -> dict:
        with trace_step("validate update payload", kind="validation", detail="Exclude empty fields"):
            payload = model_payload(update, exclude_none=True)
        if not payload:
            return self.get_ticket(ticket_id)

        with connect_ticket_store() as store:
            repository = TicketRepository(store)
            updated = repository.update(ticket_id, payload)
        if updated is None:
            raise HTTPException(status_code=404, detail="Ticket not found")
        return updated

    @traced("TicketService.delete_ticket", kind="service")
    def delete_ticket(self, ticket_id: int) -> None:
        with connect_ticket_store() as store:
            repository = TicketRepository(store)
            deleted = repository.delete(ticket_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Ticket not found")
