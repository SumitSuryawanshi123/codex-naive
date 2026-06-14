# TraceFlow

TraceFlow is a developer debugging tool for Python FastAPI backends. It records how an API request moves through route handlers, service functions, repositories, database helpers, and ordinary project functions, then displays the execution flow in a browser UI.

The CRM ticket API in this repo is only a built-in demo. The main product path is uploading a zipped FastAPI project and running that project under TraceFlow instrumentation.

## What TraceFlow Can Do

- Upload a `.zip` file containing a FastAPI codebase.
- Safely extract the zip into a local TraceFlow workspace.
- Auto-detect common FastAPI app targets such as `app.main:app` or `main:app`.
- Accept an explicit ASGI target like `app.main:create_app()`.
- Launch the uploaded app on a local port through a TraceFlow runtime wrapper.
- Discover routes from the uploaded app.
- Send GET, POST, PUT, PATCH, and DELETE requests to the uploaded app.
- Show a visual trace for each request.
- Automatically capture function calls from files inside the uploaded project.

## Project Structure

```text
code-tracker/
  traceflow/
    app.py                  # Main TraceFlow host app and UI server
    runtime.py              # Wrapper used to run uploaded FastAPI apps
    tracing/                # Middleware, recorder, decorators, profiler
    projects/               # Zip upload, extraction, app discovery, proxy calls
    demo/                   # CRM ticket demo backend
    static/                 # Browser UI
  tests/
```

## Run Locally

```bash
cd code-tracker
pip install -r requirements.txt
python -m uvicorn traceflow.app:app --host 127.0.0.1 --port 8011
```

Open `http://127.0.0.1:8011`.

If you prefer the original reload command:

```bash
uvicorn traceflow.app:app --reload --port 8010
```

Open `http://127.0.0.1:8010`.

## Upload A FastAPI Project

This repo includes a demo `app.zip` at `../app.zip` that you can upload first for testing.

1. Zip the project folder.
2. Open TraceFlow.
3. Select the zip.
4. Optionally enter an ASGI target such as:

```text
app.main:app
app.main:create_app()
main:app
```

5. Click `Upload & Run`.
6. Pick a detected route or enter a method/path manually.
7. Send the request and inspect the trace.

Uploaded apps run as local Python processes. Only upload code you trust.

## Watch The Uploaded App UI

After upload, TraceFlow shows two links:

- `Open App`: opens the uploaded FastAPI app on its own local runtime URL.
- `Open Monitor`: opens `/monitor?project_id=...`, a live simulation page.

Use them as two tabs:

1. Open the uploaded app tab.
2. Open the monitor tab.
3. Click buttons in the uploaded app, such as `Create ticket`.
4. The monitor automatically displays the latest API flow.

This works because the uploaded app is served by TraceFlow's runtime wrapper. The app keeps its own `/`, `/static`, and `/api` paths, while the monitor polls TraceFlow's runtime trace endpoint.

## How Automatic Function Tracing Works

TraceFlow wraps the uploaded ASGI app with `TraceMiddleware` and enables a lightweight profiler for files under the uploaded project root. For every request, it records Python function calls from that project and classifies them by path:

- `api` or `routes` files become route spans.
- `services` files become service spans.
- `repositories` files become repository spans.
- `db` or `database` files become database spans.
- Other project files become function spans.

You can still use explicit instrumentation when you want cleaner names or custom steps:

```python
from traceflow.tracing import traced, trace_step


@traced("BillingService.create_invoice", kind="service")
def create_invoice(payload: dict) -> dict:
    with trace_step("insert invoice row", kind="database"):
        return {"id": 1, **payload}
```

## API Endpoints

TraceFlow host:

```text
POST /api/projects/upload
GET  /api/projects
GET  /api/projects/{project_id}/routes
POST /api/projects/{project_id}/request
GET  /api/projects/{project_id}/traces/{trace_id}
```

Built-in CRM demo:

```text
POST   /api/tickets
GET    /api/tickets
PATCH  /api/tickets/{ticket_id}
DELETE /api/tickets/{ticket_id}
GET    /api/traces/{trace_id}
```

## Current Limits

- Dependencies for uploaded apps must already be available in the current Python environment.
- Uploaded code is executed locally, so use trusted projects only.
- Function profiling is optimized for debugging simulations, not production traffic.
