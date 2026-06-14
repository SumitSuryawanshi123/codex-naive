# CRM Tickets Demo

A small FastAPI + SQLite CRM ticket management demo with a browser UI and a layered backend structure.

## Run

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000 in your browser.

The SQLite database is created automatically at `app/data/crm_tickets.db` and seeded with dummy customers, agents, tickets, and comments on first startup.

You can override the database path with:

```bash
set CRM_DATABASE_PATH=C:\path\to\crm_tickets.db
```

## Project Structure

```text
app/
  api/              FastAPI routers, dependencies, and error handlers
  core/             App configuration
  db/               SQLite connection, schema, startup initialization, seed data
  models/           Pydantic request and response models
  repositories/     Database query classes
  services/         Business logic and validation
  static/           Browser UI assets
  main.py           FastAPI application factory
```

`app/database.py` remains as a small compatibility shim for older imports. New backend code should use `app.db`, `app.repositories`, and `app.services`.

## API

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
