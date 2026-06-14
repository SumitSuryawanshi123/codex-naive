# DebugOS Investigation Engine

Runnable Phase 0-1 vertical slice for investigating logs and stack traces.

## What is included

- FastAPI app with REST endpoints and a server-rendered demo UI.
- SQLite + SQLAlchemy data model for investigations, artifacts, evidence, hypotheses, links, evidence requests, and feedback.
- Deterministic ingestion: log normalization, stack-trace parsing, redaction, fingerprinting, deduplication, and provenance spans.
- Offline-friendly reasoning fallback with OpenAI-ready cached client wrapper.
- Deterministic citation verification and evidence scoring.
- Eval harness with labeled incident fixtures.

## Run

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000.

## Test and evaluate

```powershell
pytest
python -m eval.runner
```
