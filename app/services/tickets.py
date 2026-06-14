from __future__ import annotations

import os
import sqlite3

from pydantic import BaseModel

from app.models.tickets import CommentCreate, TicketCreate, TicketFilters, TicketUpdate
from app.repositories.agents import AgentRepository
from app.repositories.customers import CustomerRepository
from app.repositories.tickets import TicketRepository
from app.services.exceptions import NotFoundError, ValidationError
from app.utils.datetime import utc_now


REQUIRED_TICKET_FIELDS = {"subject", "description", "status", "priority", "category", "source", "customer_id"}
EXPORT_SCOPES = {"export:admin", "billing:export"}


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

    def export_invoice(self, ticket_id: int, authorization: str | None, scenario: str | None = None) -> dict:
        """Intentionally buggy export path for DebugOS / Fix This demos."""
        ticket = self._get_ticket_or_raise(ticket_id)
        customer = self._get_customer_or_raise(ticket["customer_id"])
        self._authorize_invoice_export(authorization)
        billing_profile = self._load_customer_billing_profile(customer, scenario)
        return self._submit_invoice_to_billing_provider(ticket, customer, billing_profile, scenario)

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

    def _get_customer_or_raise(self, customer_id: int) -> dict:
        customer = self.customers.get(customer_id)
        if not customer:
            raise NotFoundError("Customer not found")
        return customer

    def _authorize_invoice_export(self, authorization: str | None) -> None:
        if not authorization:
            raise ValidationError("403 forbidden permission denied: missing bearer token")
        lowered = authorization.lower()
        if "bearer" not in lowered:
            raise ValidationError("401 unauthorized invalid authorization header")
        if not any(scope in authorization for scope in EXPORT_SCOPES):
            raise ValidationError("403 forbidden permission denied missing scope export:admin")

    def _load_customer_billing_profile(self, customer: dict, scenario: str | None) -> dict:
        if scenario == "missing_config":
            secret = os.environ.get("BILLING_EXPORT_SECRET")
            if not secret:
                raise RuntimeError("missing env BILLING_EXPORT_SECRET invalid setting for billing export")
        if scenario == "billing_timeout":
            return {"tax_id": "demo-tax-id"}
        return customer["billing_profile"]

    def _submit_invoice_to_billing_provider(
        self,
        ticket: dict,
        customer: dict,
        billing_profile: dict,
        scenario: str | None,
    ) -> dict:
        if scenario == "billing_timeout":
            raise TimeoutError("timeout calling Stripe billing export after 30000ms")
        return {
            "ticket_id": ticket["id"],
            "customer_id": customer["id"],
            "tax_id": billing_profile["tax_id"],
            "status": "exported",
        }

    def _reject_null_required_fields(self, payload: dict) -> None:
        null_required_fields = sorted(field for field in REQUIRED_TICKET_FIELDS if field in payload and payload[field] is None)
        if null_required_fields:
            fields = ", ".join(null_required_fields)
            raise ValidationError(f"These fields cannot be null: {fields}")
