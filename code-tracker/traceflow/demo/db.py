from __future__ import annotations

from contextlib import contextmanager
from threading import RLock
from typing import Iterator

from .models import now_utc
from ..tracing import traced, trace_step


class TicketStore:
    def __init__(self) -> None:
        self._lock = RLock()
        self._next_id = 2
        created_at = now_utc()
        self._tickets: dict[int, dict] = {
            1: {
                "id": 1,
                "subject": "Demo onboarding issue",
                "description": "Customer cannot finish the first workspace setup step.",
                "customer": "Acme Ops",
                "priority": "high",
                "status": "open",
                "created_at": created_at,
                "updated_at": created_at,
            }
        }

    @traced("TicketStore.insert_ticket", kind="database", detail="INSERT tickets")
    def insert_ticket(self, payload: dict) -> dict:
        with trace_step("execute INSERT", kind="database", detail="tickets table"):
            with self._lock:
                ticket_id = self._next_id
                self._next_id += 1
                timestamp = now_utc()
                record = {
                    "id": ticket_id,
                    "status": "open",
                    "created_at": timestamp,
                    "updated_at": timestamp,
                    **payload,
                }
                self._tickets[ticket_id] = record
                return dict(record)

    @traced("TicketStore.select_ticket", kind="database", detail="SELECT ticket by id")
    def select_ticket(self, ticket_id: int) -> dict | None:
        with trace_step("execute SELECT", kind="database", detail="WHERE id = :ticket_id"):
            with self._lock:
                record = self._tickets.get(ticket_id)
                return dict(record) if record else None

    @traced("TicketStore.select_tickets", kind="database", detail="SELECT ticket list")
    def select_tickets(self) -> list[dict]:
        with trace_step("execute SELECT", kind="database", detail="ORDER BY updated_at DESC"):
            with self._lock:
                return [dict(ticket) for ticket in sorted(self._tickets.values(), key=lambda item: item["updated_at"], reverse=True)]

    @traced("TicketStore.update_ticket", kind="database", detail="UPDATE tickets")
    def update_ticket(self, ticket_id: int, payload: dict) -> dict | None:
        with trace_step("execute UPDATE", kind="database", detail="SET provided fields"):
            with self._lock:
                record = self._tickets.get(ticket_id)
                if record is None:
                    return None
                record.update(payload)
                record["updated_at"] = now_utc()
                return dict(record)

    @traced("TicketStore.delete_ticket", kind="database", detail="DELETE ticket")
    def delete_ticket(self, ticket_id: int) -> bool:
        with trace_step("execute DELETE", kind="database", detail="WHERE id = :ticket_id"):
            with self._lock:
                return self._tickets.pop(ticket_id, None) is not None


ticket_store = TicketStore()


@contextmanager
def connect_ticket_store() -> Iterator[TicketStore]:
    with trace_step("db connection", kind="database", detail="Acquire demo ticket store"):
        yield ticket_store
