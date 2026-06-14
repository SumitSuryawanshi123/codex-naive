from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel


BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE_PATH = BASE_DIR / "data" / "crm_tickets.db"


class Settings(BaseModel):
    app_name: str = "CRM Tickets Demo API"
    app_version: str = "1.0.0"
    database_path: Path = DEFAULT_DATABASE_PATH
    static_dir: Path = BASE_DIR / "static"


@lru_cache
def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv("CRM_APP_NAME", "CRM Tickets Demo API"),
        app_version=os.getenv("CRM_APP_VERSION", "1.0.0"),
        database_path=Path(os.getenv("CRM_DATABASE_PATH", str(DEFAULT_DATABASE_PATH))),
        static_dir=Path(os.getenv("CRM_STATIC_DIR", str(BASE_DIR / "static"))),
    )
