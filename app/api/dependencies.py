from __future__ import annotations

import sqlite3

from fastapi import Depends

from app.db.connection import get_db
from app.services.lookups import LookupService
from app.services.stats import StatsService
from app.services.tickets import TicketService


def get_lookup_service(connection: sqlite3.Connection = Depends(get_db)) -> LookupService:
    return LookupService(connection)


def get_stats_service(connection: sqlite3.Connection = Depends(get_db)) -> StatsService:
    return StatsService(connection)


def get_ticket_service(connection: sqlite3.Connection = Depends(get_db)) -> TicketService:
    return TicketService(connection)
