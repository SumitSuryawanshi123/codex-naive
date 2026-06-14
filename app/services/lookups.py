from __future__ import annotations

import sqlite3

from app.repositories.agents import AgentRepository
from app.repositories.customers import CustomerRepository


class LookupService:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.agents = AgentRepository(connection)
        self.customers = CustomerRepository(connection)

    def list_agents(self) -> list[dict]:
        return self.agents.list()

    def list_customers(self) -> list[dict]:
        return self.customers.list()
