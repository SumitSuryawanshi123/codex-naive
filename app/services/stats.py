from __future__ import annotations

import sqlite3

from app.repositories.stats import StatsRepository


class StatsService:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.stats = StatsRepository(connection)

    def dashboard(self) -> dict:
        return self.stats.dashboard()
