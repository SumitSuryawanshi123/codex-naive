from pydantic import BaseModel, Field


class InvestigationCreate(BaseModel):
    budget: int | None = Field(default=None, ge=1, le=12)
    summary: str | None = None


class ArtifactIn(BaseModel):
    type: str = "log"
    raw_text: str
    source_meta: dict = Field(default_factory=dict)


class FeedbackIn(BaseModel):
    chosen_root_cause: str
    was_correct: bool
    resolution_note: str = ""


class InvestigationOut(BaseModel):
    id: int
    status: str
    step_count: int
    budget: int
    summary: str | None
