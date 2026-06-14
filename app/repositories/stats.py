from __future__ import annotations

import sqlite3


class StatsRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def dashboard(self) -> dict:
        total = self.connection.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
        by_status = self.connection.execute(
            "SELECT status, COUNT(*) AS count FROM tickets GROUP BY status ORDER BY status"
        ).fetchall()
        by_priority = self.connection.execute(
            "SELECT priority, COUNT(*) AS count FROM tickets GROUP BY priority ORDER BY priority"
        ).fetchall()
        urgent_open = self.connection.execute(
            """
            SELECT COUNT(*)
            FROM tickets
            WHERE priority = 'Urgent' AND status NOT IN ('Resolved', 'Closed')
            """
        ).fetchone()[0]

        return {
            "total": total,
            "urgent_open": urgent_open,
            "by_status": {row["status"]: row["count"] for row in by_status},
            "by_priority": {row["priority"]: row["count"] for row in by_priority},
        }
