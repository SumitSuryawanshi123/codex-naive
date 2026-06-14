from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


TicketStatus = Literal["Open", "In Progress", "Pending Customer", "Resolved", "Closed"]
TicketPriority = Literal["Low", "Medium", "High", "Urgent"]


class TicketCreate(BaseModel):
    subject: str = Field(min_length=3, max_length=160)
    description: str = Field(min_length=5, max_length=2000)
    status: TicketStatus = "Open"
    priority: TicketPriority = "Medium"
    category: str = Field(default="General", min_length=2, max_length=80)
    source: str = Field(default="Portal", min_length=2, max_length=80)
    customer_id: int
    agent_id: int | None = None
    due_at: str | None = None


class TicketUpdate(BaseModel):
    subject: str | None = Field(default=None, min_length=3, max_length=160)
    description: str | None = Field(default=None, min_length=5, max_length=2000)
    status: TicketStatus | None = None
    priority: TicketPriority | None = None
    category: str | None = Field(default=None, min_length=2, max_length=80)
    source: str | None = Field(default=None, min_length=2, max_length=80)
    customer_id: int | None = None
    agent_id: int | None = None
    due_at: str | None = None


class TicketFilters(BaseModel):
    status: TicketStatus | None = None
    priority: TicketPriority | None = None
    agent_id: int | None = None
    q: str | None = Field(default=None, max_length=100)


class CommentCreate(BaseModel):
    author: str = Field(min_length=2, max_length=120)
    body: str = Field(min_length=3, max_length=1000)


class ExportInvoiceRequest(BaseModel):
    authorization: str | None = Field(
        default=None,
        description="Bearer token used for invoice export authorization checks.",
    )


class Comment(BaseModel):
    id: int
    ticket_id: int
    author: str
    body: str
    created_at: str


class TicketSummary(BaseModel):
    id: int
    subject: str
    description: str
    status: TicketStatus
    priority: TicketPriority
    category: str
    source: str
    customer_id: int
    agent_id: int | None = None
    due_at: str | None = None
    created_at: str
    updated_at: str
    customer_name: str
    customer_company: str
    customer_email: str
    customer_tier: str
    agent_name: str | None = None
    agent_role: str | None = None


class TicketDetail(TicketSummary):
    comments: list[Comment] = Field(default_factory=list)
