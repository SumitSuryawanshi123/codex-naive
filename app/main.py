from __future__ import annotations

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db, init_db
from app.evidence.store import append_artifact
from app.learning import record_resolution
from app.models import Feedback, Investigation
from app.orchestrator import create_investigation, step_investigation
from app.report import investigation_report
from app.schemas import ArtifactIn, FeedbackIn, InvestigationCreate, InvestigationOut

app = FastAPI(title="DebugOS Investigation Engine")
templates = Jinja2Templates(directory="app/templates")


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/demo", response_class=HTMLResponse)
def demo_submit(
    request: Request,
    raw_text: str = Form(...),
    summary: str = Form(""),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    inv = create_investigation(db, summary=summary or None)
    append_artifact(db, inv.id, "log", raw_text, {"source": "demo_form"})
    step_investigation(db, inv.id)
    return templates.TemplateResponse("report.html", {"request": request, "report": investigation_report(db, inv.id)})


@app.post("/investigations", response_model=InvestigationOut)
def create(payload: InvestigationCreate, db: Session = Depends(get_db)) -> Investigation:
    return create_investigation(db, payload.budget, payload.summary)


@app.post("/investigations/{investigation_id}/evidence")
def add_evidence(investigation_id: int, payload: ArtifactIn, db: Session = Depends(get_db)) -> dict:
    if not db.get(Investigation, investigation_id):
        raise HTTPException(status_code=404, detail="investigation not found")
    artifact = append_artifact(db, investigation_id, payload.type, payload.raw_text, payload.source_meta)
    return {"artifact_id": artifact.id}


@app.post("/investigations/{investigation_id}/step", response_model=InvestigationOut)
def step(investigation_id: int, db: Session = Depends(get_db)) -> Investigation:
    try:
        return step_investigation(db, investigation_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/investigations/{investigation_id}/report")
def report(investigation_id: int, db: Session = Depends(get_db)) -> dict:
    try:
        return investigation_report(db, investigation_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/investigations/{investigation_id}/feedback")
def feedback(investigation_id: int, payload: FeedbackIn, db: Session = Depends(get_db)) -> dict:
    if not db.get(Investigation, investigation_id):
        raise HTTPException(status_code=404, detail="investigation not found")
    item = Feedback(investigation_id=investigation_id, **payload.model_dump())
    db.add(item)
    db.flush()
    record_resolution(db, item)
    db.commit()
    return {"ok": True}


@app.post("/demo/{investigation_id}/feedback")
def demo_feedback(
    investigation_id: int,
    chosen_root_cause: str = Form(...),
    was_correct: bool = Form(False),
    resolution_note: str = Form(""),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    item = Feedback(
        investigation_id=investigation_id,
        chosen_root_cause=chosen_root_cause,
        was_correct=was_correct,
        resolution_note=resolution_note,
    )
    db.add(item)
    db.flush()
    record_resolution(db, item)
    db.commit()
    return RedirectResponse("/", status_code=303)
