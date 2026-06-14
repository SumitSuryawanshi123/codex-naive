from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


Priority = Literal["low", "medium", "high", "urgent"]
TicketStatus = Literal["open", "waiting", "resolved", "closed"]


class TicketCreate(BaseModel):
    subject: str = Field(min_length=3, max_length=120)
    description: str = Field(min_length=8, max_length=1000)
    customer: str = Field(min_length=2, max_length=80)
    priority: Priority = "medium"


class TicketUpdate(BaseModel):
    subject: str | None = Field(default=None, min_length=3, max_length=120)
    description: str | None = Field(default=None, min_length=8, max_length=1000)
    priority: Priority | None = None
    status: TicketStatus | None = None


class Ticket(BaseModel):
    id: int
    subject: str
    description: str
    customer: str
    priority: Priority
    status: TicketStatus
    created_at: datetime
    updated_at: datetime


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def model_payload(model: BaseModel, *, exclude_none: bool = False) -> dict:
    if hasattr(model, "model_dump"):
        return model.model_dump(exclude_none=exclude_none)
    return model.dict(exclude_none=exclude_none)
