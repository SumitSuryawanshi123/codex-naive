from __future__ import annotations

from ..db import TicketStore
from ...tracing import traced, trace_step


class TicketRepository:
    def __init__(self, store: TicketStore) -> None:
        self.store = store

    @traced("TicketRepository.create", kind="repository")
    def create(self, payload: dict) -> dict:
        with trace_step("prepare insert payload", kind="repository", detail="Normalize ticket fields"):
            normalized = dict(payload)
        return self.store.insert_ticket(normalized)

    @traced("TicketRepository.get", kind="repository")
    def get(self, ticket_id: int) -> dict | None:
        return self.store.select_ticket(ticket_id)

    @traced("TicketRepository.list", kind="repository")
    def list(self) -> list[dict]:
        return self.store.select_tickets()

    @traced("TicketRepository.update", kind="repository")
    def update(self, ticket_id: int, payload: dict) -> dict | None:
        with trace_step("prepare update payload", kind="repository", detail="Drop unchanged fields"):
            update_payload = {key: value for key, value in payload.items() if value is not None}
        return self.store.update_ticket(ticket_id, update_payload)

    @traced("TicketRepository.delete", kind="repository")
    def delete(self, ticket_id: int) -> bool:
        return self.store.delete_ticket(ticket_id)
