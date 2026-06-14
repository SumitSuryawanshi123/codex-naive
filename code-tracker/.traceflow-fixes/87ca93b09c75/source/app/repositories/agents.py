from __future__ import annotations

import sqlite3


class AgentRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def list(self) -> list[dict]:
        rows = self.connection.execute(
            "SELECT id, name, email, role FROM agents ORDER BY name"
        ).fetchall()
        return [dict(row) for row in rows]

    def exists(self, agent_id: int) -> bool:
        row = self.connection.execute("SELECT id FROM agents WHERE id = ?", (agent_id,)).fetchone()
        return row is not None
