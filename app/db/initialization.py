from __future__ import annotations

from .connection import create_connection
from .schema import SCHEMA_SQL
from .seed import seed_database


def initialize_database() -> None:
    connection = create_connection()
    try:
        connection.executescript(SCHEMA_SQL)
        ticket_count = connection.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
        if not ticket_count:
            seed_database(connection)
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
