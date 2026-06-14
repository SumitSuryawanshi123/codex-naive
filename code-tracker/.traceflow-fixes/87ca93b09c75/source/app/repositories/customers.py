from __future__ import annotations

import sqlite3


class CustomerRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def list(self) -> list[dict]:
        rows = self.connection.execute(
            "SELECT id, name, company, email, phone, tier FROM customers ORDER BY company"
        ).fetchall()
        return [dict(row) for row in rows]

    def exists(self, customer_id: int) -> bool:
        row = self.connection.execute("SELECT id FROM customers WHERE id = ?", (customer_id,)).fetchone()
        return row is not None

    def get(self, customer_id: int) -> dict | None:
        row = self.connection.execute(
            "SELECT id, name, company, email, phone, tier FROM customers WHERE id = ?",
            (customer_id,),
        ).fetchone()
        return dict(row) if row else None
