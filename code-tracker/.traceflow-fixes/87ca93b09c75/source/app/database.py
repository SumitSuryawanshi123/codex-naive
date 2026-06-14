"""Backward-compatible imports for older local scripts."""

from .db.connection import create_connection as get_connection
from .db.initialization import initialize_database
from .utils.datetime import utc_now

__all__ = ["get_connection", "initialize_database", "utc_now"]
