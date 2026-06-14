from __future__ import annotations

import json
import os
import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4

from ..projects.manager import ProjectError, project_manager


TRACEFLOW_ROOT = Path(__file__).resolve().parents[2]
FIX_WORKSPACE_DIR = TRACEFLOW_ROOT / ".traceflow-fixes"
MAX_CONTEXT_CHARS = 70000
MAX_FILE_CHARS = 14000


class AnalysisError(RuntimeError):
    pass


@dataclass
class SourceReference:
    path: str
    line: int | None
    content: str


def analyze_trace(
    *,
    trace: dict[str, Any],
    query: str | None,
    project_id: str | None,
) -> dict[str, Any]:
    graph = build_trace_graph(trace)
    sources = collect_source_references(trace, project_id)
    ai_payload = _call_analysis_model(trace=trace, graph=graph, sources=sources, query=query)
    return {
        **graph,
        "query": query or "",
        "summary": ai_payload.get("summary") or _fallback_summary(trace),
        "failure_points": ai_payload.get("failure_points") or _fallback_failure_points(trace),
        "llm_used": bool(ai_payload.get("llm_used")),
        "llm_error": ai_payload.get("llm_error"),
        "model": ai_payload.get("model"),
        "nodes": _merge_node_explanations(graph["nodes"], ai_payload.get("nodes") or []),
    }


def elaborate_node(
    *,
    trace: dict[str, Any],
    node: dict[str, Any],
    query: str | None,
    project_id: str | None,
) -> dict[str, Any]:
    sources: list[SourceReference] = []
    source = node.get("source") if isinstance(node.get("source"), dict) else None
    if project_id and source and source.get("path"):
        try:
            source_dir = project_manager.get_project(project_id).source_dir
            path = _safe_child_path(source_dir, str(source["path"]))
            if path.exists() and path.is_file():
                sources.append(
                    SourceReference(
                        path=str(source["path"]),
                        line=source.get("line"),
                        content=path.read_text(encoding="utf-8", errors="replace")[:MAX_FILE_CHARS],
                    )
                )
        except (ProjectError, AnalysisError):
            sources = []

    ai_payload = _call_elaboration_model(trace=trace, node=node, sources=sources, query=query)
    return {
        "node_id": node.get("id"),
        "title": node.get("name") or node.get("label") or "Trace step",
        "markdown": ai_payload.get("markdown") or _fallback_elaboration(node, sources),
        "llm_used": bool(ai_payload.get("llm_used")),
        "llm_error": ai_payload.get("llm_error"),
        "model": ai_payload.get("model"),
    }


def create_fix_zip(
    *,
    trace: dict[str, Any],
    query: str | None,
    project_id: str | None,
    analysis: dict[str, Any] | None,
) -> Path:
    fix_id = uuid4().hex[:12]
    fix_dir = FIX_WORKSPACE_DIR / fix_id
    source_copy = fix_dir / "source"
    zip_path = fix_dir / "traceflow-fix.zip"
    fix_dir.mkdir(parents=True, exist_ok=True)

    if not project_id:
        _write_notes_zip(
            zip_path,
            "No uploaded project was attached to this trace, so TraceFlow could not produce edited source files.\n\n"
            f"Query: {query or 'No query provided'}\n\n"
            f"Trace: {trace.get('title') or trace.get('path') or 'unknown'}\n",
        )
        return zip_path

    try:
        session = project_manager.get_project(project_id)
    except ProjectError as exc:
        raise AnalysisError(str(exc)) from exc

    shutil.copytree(session.source_dir, source_copy, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", ".mypy_cache"))
    sources = collect_repair_sources(source_copy, trace)
    repair = _call_repair_model(trace=trace, query=query, analysis=analysis, sources=sources)

    files = repair.get("files") if isinstance(repair, dict) else None
    if files:
        for file_patch in files:
            relative_path = str(file_patch.get("path") or "").strip()
            content = file_patch.get("content")
            if not relative_path or not isinstance(content, str):
                continue
            target = _safe_child_path(source_copy, relative_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")

        notes = repair.get("notes") or []
        if notes:
            (fix_dir / "FIX_NOTES.md").write_text(_markdown_list("Fix notes", notes), encoding="utf-8")
    else:
        (fix_dir / "FIX_NOTES.md").write_text(
            "OpenAI did not return editable files. The project source is included unchanged.\n",
            encoding="utf-8",
        )

    _zip_directory(source_copy, zip_path)
    return zip_path


def build_trace_graph(trace: dict[str, Any]) -> dict[str, Any]:
    root_id = f"trace-{trace.get('trace_id') or 'request'}"
    nodes = [
        {
            "id": root_id,
            "label": trace.get("title") or f"{trace.get('method', '')} {trace.get('path', '')}".strip(),
            "kind": "request",
            "detail": f"HTTP {trace.get('method', '-')} {trace.get('path', '-')}",
            "status": trace.get("outcome") or "running",
            "duration_ms": trace.get("duration_ms"),
            "markdown": "\n".join(
                [
                    "- Entry point for the traced HTTP request.",
                    f"- Method/path: `{trace.get('method', '-')} {trace.get('path', '-')}`.",
                    f"- Response status: `{trace.get('status_code') or '-'}`.",
                    f"- Total duration: `{trace.get('duration_ms') if trace.get('duration_ms') is not None else '-'} ms`.",
                ]
            ),
        }
    ]
    edges: list[dict[str, str]] = []
    seen = {root_id}

    for event in trace.get("events") or []:
        event_id = str(event.get("event_id"))
        if not event_id or event_id in seen:
            continue
        detail = event.get("detail") or ""
        nodes.append(
            {
                "id": event_id,
                "label": _short_name(str(event.get("name") or "unnamed")),
                "name": event.get("name"),
                "kind": event.get("kind") or "function",
                "detail": detail,
                "status": event.get("status") or "unknown",
                "duration_ms": event.get("duration_ms"),
                "source": _source_from_detail(detail),
                "markdown": _heuristic_node_text(event),
            }
        )
        parent_id = event.get("parent_id") or root_id
        edges.append({"from": str(parent_id), "to": event_id})
        seen.add(event_id)

    return {"nodes": nodes, "edges": edges}


def collect_source_references(trace: dict[str, Any], project_id: str | None) -> list[SourceReference]:
    if not project_id:
        return []
    try:
        source_dir = project_manager.get_project(project_id).source_dir
    except ProjectError:
        return []
    return _collect_sources_from_root(source_dir, trace)


def collect_repair_sources(source_dir: Path, trace: dict[str, Any]) -> dict[str, str]:
    focused = {ref.path for ref in _collect_sources_from_root(source_dir, trace)}
    if not focused:
        focused = {
            str(path.relative_to(source_dir))
            for path in source_dir.rglob("*.py")
            if "__pycache__" not in path.parts
        }
    payload: dict[str, str] = {}
    total = 0
    for relative in sorted(focused):
        path = _safe_child_path(source_dir, relative)
        if not path.exists() or not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")[:MAX_FILE_CHARS]
        if total + len(text) > MAX_CONTEXT_CHARS:
            break
        payload[relative] = text
        total += len(text)
    return payload


def _collect_sources_from_root(source_dir: Path, trace: dict[str, Any]) -> list[SourceReference]:
    references: list[SourceReference] = []
    seen: set[str] = set()
    for event in trace.get("events") or []:
        source = _source_from_detail(str(event.get("detail") or ""))
        if not source or source["path"] in seen:
            continue
        try:
            path = _safe_child_path(source_dir, source["path"])
        except AnalysisError:
            continue
        if not path.exists() or not path.is_file():
            continue
        references.append(
            SourceReference(
                path=source["path"],
                line=source.get("line"),
                content=path.read_text(encoding="utf-8", errors="replace")[:MAX_FILE_CHARS],
            )
        )
        seen.add(source["path"])
    return references


def _call_analysis_model(
    *,
    trace: dict[str, Any],
    graph: dict[str, Any],
    sources: list[SourceReference],
    query: str | None,
) -> dict[str, Any]:
    prompt = {
        "task": "Explain this FastAPI request trace as a node graph and identify likely break/failure points.",
        "user_query": query or "",
        "trace": trace,
        "graph": graph,
        "sources": [source.__dict__ for source in sources],
        "output_contract": {
            "summary": "2-4 sentence markdown summary",
            "nodes": [
                {
                    "id": "node id",
                    "markdown": "3-4 concise markdown bullets explaining what this node does, what data it handles, and why it matters",
                }
            ],
            "failure_points": [{"node_id": "node id", "reason": "why it may fail", "confidence": "low|medium|high"}],
        },
    }
    return _call_openai_json(prompt, default={})


def _call_elaboration_model(
    *,
    trace: dict[str, Any],
    node: dict[str, Any],
    sources: list[SourceReference],
    query: str | None,
) -> dict[str, Any]:
    prompt = {
        "task": (
            "Explain this single trace graph node in depth. Use the function/file source when available. "
            "Prefer practical debugging context over generic wording."
        ),
        "user_query": query or "",
        "trace": trace,
        "node": node,
        "sources": [source.__dict__ for source in sources],
        "output_contract": {
            "markdown": "Markdown with: What it does, Inputs/outputs, Dependencies, Failure modes, and Debugging next steps.",
        },
    }
    return _call_openai_json(prompt, default={})


def _call_repair_model(
    *,
    trace: dict[str, Any],
    query: str | None,
    analysis: dict[str, Any] | None,
    sources: dict[str, str],
) -> dict[str, Any]:
    prompt = {
        "task": (
            "Fix the likely bug in this FastAPI project. Return complete replacement file contents "
            "only for files that need changes. Do not invent unrelated refactors."
        ),
        "user_query": query or "",
        "trace": trace,
        "analysis": analysis or {},
        "source_files": sources,
        "output_contract": {
            "files": [{"path": "relative/path.py", "content": "complete new file content", "explanation": "brief reason"}],
            "notes": ["short markdown notes"],
        },
    }
    return _call_openai_json(prompt, default={})


def _call_openai_json(payload: dict[str, Any], *, default: dict[str, Any]) -> dict[str, Any]:
    _load_local_env()
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key or api_key == "replace-with-your-openai-api-key":
        return {**default, "llm_error": "OPENAI_API_KEY is missing or still set to the placeholder value."}
    try:
        from openai import OpenAI  # type: ignore
    except ImportError:
        return {**default, "llm_error": "The openai Python package is not installed. Run pip install -r requirements.txt."}

    model = os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")
    client = OpenAI(api_key=api_key)
    try:
        response = client.responses.create(
            model=model,
            input=(
                "You are TraceFlow's code-analysis assistant. Return only valid JSON matching the requested "
                "output_contract. Keep node explanations concise.\n\n"
                + json.dumps(payload, ensure_ascii=False)
            ),
        )
        text = getattr(response, "output_text", "") or ""
        parsed = _parse_json_object(text)
        if isinstance(parsed, dict):
            parsed["llm_used"] = True
            parsed["model"] = model
            return parsed
    except Exception:
        return {**default, "llm_error": "OpenAI request failed. Check the API key, model name, network access, and account access."}
    return default


def _load_local_env() -> None:
    env_path = TRACEFLOW_ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _parse_json_object(text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start : end + 1])
        raise


def _source_from_detail(detail: str) -> dict[str, Any] | None:
    if ".py:" not in detail:
        return None
    path_part, line_part = detail.rsplit(":", 1)
    try:
        line = int(line_part)
    except ValueError:
        line = None
    return {"path": path_part.replace("\\", "/"), "line": line}


def _safe_child_path(root: Path, relative_path: str) -> Path:
    target = (root / relative_path).resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError as exc:
        raise AnalysisError(f"Unsafe path rejected: {relative_path}") from exc
    return target


def _merge_node_explanations(nodes: list[dict[str, Any]], ai_nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    markdown_by_id = {
        str(node.get("id")): str(node.get("markdown"))
        for node in ai_nodes
        if node.get("id") and node.get("markdown")
    }
    return [{**node, "markdown": markdown_by_id.get(node["id"], node.get("markdown", ""))} for node in nodes]


def _fallback_summary(trace: dict[str, Any]) -> str:
    outcome = trace.get("outcome") or "unknown"
    status = trace.get("status_code") or "-"
    return f"TraceFlow captured `{trace.get('title') or trace.get('path')}` with outcome `{outcome}` and status `{status}`."


def _fallback_failure_points(trace: dict[str, Any]) -> list[dict[str, str]]:
    failures = [
        {
            "node_id": event.get("event_id"),
            "reason": event.get("error") or "This span reported an error status.",
            "confidence": "high",
        }
        for event in trace.get("events") or []
        if event.get("status") == "error" or event.get("error")
    ]
    if failures:
        return failures
    if trace.get("status_code") and int(trace["status_code"]) >= 400:
        return [{"node_id": f"trace-{trace.get('trace_id')}", "reason": "The request returned an HTTP error.", "confidence": "medium"}]
    return [{"node_id": f"trace-{trace.get('trace_id')}", "reason": "No explicit error was recorded; inspect slow or unexpected spans.", "confidence": "low"}]


def _heuristic_node_text(event: dict[str, Any]) -> str:
    kind = event.get("kind") or "function"
    name = _short_name(str(event.get("name") or "step"))
    detail = event.get("detail")
    lines = [
        f"- `{name}` is a `{kind}` step in the request flow.",
        f"- It completed with status `{event.get('status') or 'unknown'}`.",
        f"- Runtime was `{event.get('duration_ms') if event.get('duration_ms') is not None else '-'} ms`.",
    ]
    if detail:
        lines.append(f"- Trace detail: {detail}.")
    else:
        lines.append("- No source detail was attached to this span.")
    return "\n".join(lines)


def _fallback_elaboration(node: dict[str, Any], sources: list[SourceReference]) -> str:
    title = node.get("name") or node.get("label") or "Trace step"
    source_note = "No source file was attached to this node."
    if sources:
        source = sources[0]
        source_note = f"Source file: `{source.path}`" + (f" near line `{source.line}`." if source.line else ".")
    return "\n".join(
        [
            f"### {title}",
            "",
            f"- Kind: `{node.get('kind') or 'function'}`.",
            f"- Status: `{node.get('status') or 'unknown'}`.",
            f"- Duration: `{node.get('duration_ms') if node.get('duration_ms') is not None else '-'} ms`.",
            f"- {source_note}",
            "- OpenAI elaboration was unavailable, so this explanation is based on captured trace metadata.",
        ]
    )


def _short_name(name: str) -> str:
    return name.split(".")[-1] if name else ""


def _markdown_list(title: str, values: list[Any]) -> str:
    lines = [f"# {title}", ""]
    for value in values:
        lines.append(f"- {value}")
    return "\n".join(lines) + "\n"


def _zip_directory(source_dir: Path, zip_path: Path) -> None:
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in source_dir.rglob("*"):
            if path.is_file():
                archive.write(path, path.relative_to(source_dir))


def _write_notes_zip(zip_path: Path, text: str) -> None:
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("FIX_NOTES.md", text)
