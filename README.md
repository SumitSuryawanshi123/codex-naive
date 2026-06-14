# DebugOS Investigation Engine + CRM Tickets Demo

This merged codebase contains both applications from the two branches:

- **DebugOS Investigation Engine**: an investigation agent for logs, traces, evidence scoring, LLM-assisted reasoning, reports, learning, and remediation suggestions.
- **CRM Tickets Demo**: a FastAPI + SQLite CRM ticket management demo with a browser UI and layered backend.

## Run

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open:

- DebugOS UI: http://127.0.0.1:8000/
- CRM Tickets UI: http://127.0.0.1:8000/crm
- API docs: http://127.0.0.1:8000/docs

## DebugOS

DebugOS includes:

- FastAPI REST endpoints and a server-rendered demo UI.
- SQLite + SQLAlchemy models for investigations, artifacts, evidence, hypotheses, evidence links, requests, feedback, resolved incidents, and learned patterns.
- Deterministic ingestion for logs, stack traces, configs, HAR, and OTel-style traces.
- Secret/PII redaction, fingerprinting, deduplication, source snippets, git blame helper, failure pattern priors, timeline reporting, learning from feedback, and remediation suggestions.
- Cached OpenAI/LLM client wrapper using `OPENAI_API_KEY` or `OPENAI_API_KEY`.

Useful commands:

```powershell
pytest
$env:ENABLE_LLM_REASONING='false'; python -m eval.runner
$env:ENABLE_LLM_REASONING='true'; python -m eval.runner
```

## CRM Tickets

The CRM SQLite database is created automatically at `app/data/crm_tickets.db` and seeded with dummy customers, agents, tickets, and comments on first startup.

Override the database path with:

```powershell
$env:CRM_DATABASE_PATH='C:\path\to\crm_tickets.db'
```

CRM project structure:

```text
app/
  api/              FastAPI routers, dependencies, and error handlers
  core/             CRM app configuration
  db/               SQLite connection, schema, startup initialization, seed data
  models/           CRM Pydantic models plus DebugOS SQLAlchemy compatibility exports
  repositories/     CRM database query classes
  services/         CRM business logic and validation
  static/           CRM browser UI assets
```

CRM API:

- `GET /api/health`
- `GET /api/stats`
- `GET /api/customers`
- `GET /api/agents`
- `GET /api/tickets`
- `GET /api/tickets/{ticket_id}`
- `POST /api/tickets`
- `PATCH /api/tickets/{ticket_id}`
- `DELETE /api/tickets/{ticket_id}`
- `POST /api/tickets/{ticket_id}/comments`
