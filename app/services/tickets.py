from __future__ import annotations

import sqlite3

from pydantic import BaseModel

from app.models.tickets import CommentCreate, TicketCreate, TicketFilters, TicketUpdate
from app.repositories.agents import AgentRepository
from app.repositories.customers import CustomerRepository
from app.repositories.tickets import TicketRepository
from app.services.exceptions import NotFoundError, ValidationError
from app.utils.datetime import utc_now


REQUIRED_TICKET_FIELDS = {"subject", "description", "status", "priority", "category", "source", "customer_id"}


def model_payload(model: BaseModel, *, exclude_unset: bool = True) -> dict:
    if hasattr(model, "model_dump"):
        return model.model_dump(exclude_unset=exclude_unset)
    return model.dict(exclude_unset=exclude_unset)


class TicketService:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.tickets = TicketRepository(connection)
        self.customers = CustomerRepository(connection)
        self.agents = AgentRepository(connection)

    def list_tickets(self, filters: TicketFilters) -> list[dict]:
        return self.tickets.list(filters)

    def get_ticket(self, ticket_id: int) -> dict:
        ticket = self._get_ticket_or_raise(ticket_id)
        ticket["comments"] = self.tickets.list_comments(ticket_id)
        return ticket

    def create_ticket(self, ticket: TicketCreate) -> dict:
        self._ensure_customer_exists(ticket.customer_id)
        self._ensure_agent_exists(ticket.agent_id)

        created_at = utc_now()
        ticket_id = self.tickets.create(model_payload(ticket, exclude_unset=False), created_at)
        return self.get_ticket(ticket_id)

    def update_ticket(self, ticket_id: int, update: TicketUpdate) -> dict:
        self._get_ticket_or_raise(ticket_id)
        payload = model_payload(update)

        if not payload:
            return self.get_ticket(ticket_id)

        self._reject_null_required_fields(payload)

        if "customer_id" in payload:
            self._ensure_customer_exists(payload["customer_id"])
        if "agent_id" in payload:
            self._ensure_agent_exists(payload["agent_id"])

        payload["updated_at"] = utc_now()
        self.tickets.update(ticket_id, payload)
        return self.get_ticket(ticket_id)

    def delete_ticket(self, ticket_id: int) -> None:
        self._get_ticket_or_raise(ticket_id)
        self.tickets.delete(ticket_id)

    def add_comment(self, ticket_id: int, comment: CommentCreate) -> dict:
        self._get_ticket_or_raise(ticket_id)
        created_at = utc_now()
        new_comment = self.tickets.add_comment(ticket_id, comment.author, comment.body, created_at)
        self.tickets.touch(ticket_id, created_at)
        return new_comment

    def _get_ticket_or_raise(self, ticket_id: int) -> dict:
        ticket = self.tickets.get(ticket_id)
        if not ticket:
            raise NotFoundError("Ticket not found")
        return ticket

    def _ensure_customer_exists(self, customer_id: int | None) -> None:
        if customer_id is None or not self.customers.exists(customer_id):
            raise ValidationError("Customer does not exist")

    def _ensure_agent_exists(self, agent_id: int | None) -> None:
        if agent_id is not None and not self.agents.exists(agent_id):
            raise ValidationError("Agent does not exist")

    def _reject_null_required_fields(self, payload: dict) -> None:
        null_required_fields = sorted(field for field in REQUIRED_TICKET_FIELDS if field in payload and payload[field] is None)
        if null_required_fields:
            fields = ", ".join(null_required_fields)
            raise ValidationError(f"These fields cannot be null: {fields}")
