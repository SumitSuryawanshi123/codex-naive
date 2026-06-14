from __future__ import annotations

import sqlite3
from typing import Any

from app.models.tickets import TicketFilters


TICKET_SELECT = """
    SELECT
        tickets.*,
        customers.name AS customer_name,
        customers.company AS customer_company,
        customers.email AS customer_email,
        customers.tier AS customer_tier,
        agents.name AS agent_name,
        agents.role AS agent_role
    FROM tickets
    JOIN customers ON customers.id = tickets.customer_id
    LEFT JOIN agents ON agents.id = tickets.agent_id
"""

UPDATEABLE_TICKET_FIELDS = (
    "subject",
    "description",
    "status",
    "priority",
    "category",
    "source",
    "customer_id",
    "agent_id",
    "due_at",
    "updated_at",
)


class TicketRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def list(self, filters: TicketFilters) -> list[dict]:
        clauses: list[str] = []
        params: list[Any] = []

        if filters.status:
            clauses.append("tickets.status = ?")
            params.append(filters.status)
        if filters.priority:
            clauses.append("tickets.priority = ?")
            params.append(filters.priority)
        if filters.agent_id is not None:
            clauses.append("tickets.agent_id = ?")
            params.append(filters.agent_id)
        if filters.q:
            clauses.append(
                """
                (
                    tickets.subject LIKE ?
                    OR tickets.description LIKE ?
                    OR customers.name LIKE ?
                    OR customers.company LIKE ?
                )
                """
            )
            search = f"%{filters.q}%"
            params.extend([search, search, search, search])

        where_clause = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        query = f"{TICKET_SELECT} {where_clause} ORDER BY tickets.updated_at DESC, tickets.id DESC"
        rows = self.connection.execute(query, tuple(params)).fetchall()
        return [dict(row) for row in rows]

    def get(self, ticket_id: int) -> dict | None:
        row = self.connection.execute(f"{TICKET_SELECT} WHERE tickets.id = ?", (ticket_id,)).fetchone()
        return dict(row) if row else None

    def create(self, data: dict, created_at: str) -> int:
        cursor = self.connection.execute(
            """
            INSERT INTO tickets (
                subject, description, status, priority, category, source,
                customer_id, agent_id, due_at, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["subject"],
                data["description"],
                data["status"],
                data["priority"],
                data["category"],
                data["source"],
                data["customer_id"],
                data.get("agent_id"),
                data.get("due_at"),
                created_at,
                created_at,
            ),
        )
        return int(cursor.lastrowid)

    def update(self, ticket_id: int, data: dict) -> None:
        fields = [field for field in UPDATEABLE_TICKET_FIELDS if field in data]
        if not fields:
            return

        assignments = ", ".join(f"{field} = ?" for field in fields)
        params = [data[field] for field in fields]
        params.append(ticket_id)
        self.connection.execute(f"UPDATE tickets SET {assignments} WHERE id = ?", tuple(params))

    def delete(self, ticket_id: int) -> None:
        self.connection.execute("DELETE FROM tickets WHERE id = ?", (ticket_id,))

    def list_comments(self, ticket_id: int) -> list[dict]:
        rows = self.connection.execute(
            """
            SELECT id, ticket_id, author, body, created_at
            FROM comments
            WHERE ticket_id = ?
            ORDER BY created_at DESC, id DESC
            """,
            (ticket_id,),
        ).fetchall()
        return [dict(row) for row in rows]

    def add_comment(self, ticket_id: int, author: str, body: str, created_at: str) -> dict:
        cursor = self.connection.execute(
            """
            INSERT INTO comments (ticket_id, author, body, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (ticket_id, author, body, created_at),
        )
        row = self.connection.execute("SELECT * FROM comments WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return dict(row)

    def touch(self, ticket_id: int, updated_at: str) -> None:
        self.connection.execute("UPDATE tickets SET updated_at = ? WHERE id = ?", (updated_at, ticket_id))
