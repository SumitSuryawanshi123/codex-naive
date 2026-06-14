from __future__ import annotations

import ast
import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import zipfile
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any
from uuid import uuid4


TRACEFLOW_ROOT = Path(__file__).resolve().parents[2]
WORKSPACE_DIR = TRACEFLOW_ROOT / ".traceflow-workspaces"
MAX_ZIP_BYTES = 30 * 1024 * 1024
MAX_ZIP_FILES = 1500
SKIPPED_DIRS = {
    ".git",
    ".hg",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "node_modules",
    "site-packages",
    "venv",
    ".venv",
}


class ProjectError(RuntimeError):
    pass


@dataclass
class ProjectSession:
    project_id: str
    name: str
    source_dir: Path
    app_target: str
    port: int
    process: subprocess.Popen[bytes]
    log_path: Path
    status: str = "running"
    routes: list[dict[str, Any]] | None = None

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    def to_dict(self) -> dict[str, Any]:
        running = self.process.poll() is None
        return {
            "project_id": self.project_id,
            "name": self.name,
            "source_dir": str(self.source_dir),
            "app_target": self.app_target,
            "port": self.port,
            "base_url": self.base_url,
            "status": self.status if running else "stopped",
            "routes": self.routes or [],
            "log_tail": self.read_log_tail(),
        }

    def read_log_tail(self, limit: int = 4000) -> str:
        if not self.log_path.exists():
            return ""
        data = self.log_path.read_text(encoding="utf-8", errors="replace")
        return data[-limit:]


class ProjectManager:
    def __init__(self, workspace_dir: Path = WORKSPACE_DIR) -> None:
        self.workspace_dir = workspace_dir
        self._sessions: dict[str, ProjectSession] = {}

    def list_projects(self) -> list[dict[str, Any]]:
        return [session.to_dict() for session in self._sessions.values()]

    def get_project(self, project_id: str) -> ProjectSession:
        session = self._sessions.get(project_id)
        if session is None:
            raise ProjectError("Project session not found")
        return session

    def stop_project(self, project_id: str) -> dict[str, Any]:
        session = self.get_project(project_id)
        if session.process.poll() is None:
            session.process.terminate()
            try:
                session.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                session.process.kill()
                session.process.wait(timeout=5)
        self._sessions.pop(project_id, None)
        return {
            "project_id": project_id,
            "status": "stopped",
        }

    def upload_zip(
        self,
        *,
        filename: str,
        data: bytes,
        app_target: str | None = None,
    ) -> ProjectSession:
        if len(data) > MAX_ZIP_BYTES:
            raise ProjectError("Zip file is too large for local tracing")
        if not zipfile.is_zipfile(BytesIO(data)):
            raise ProjectError("Upload must be a valid .zip file")

        try:
            self.workspace_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise ProjectError(f"Could not create TraceFlow workspace: {exc}") from exc

        project_id = uuid4().hex[:12]
        project_dir = self.workspace_dir / project_id
        extract_dir = project_dir / "source"
        try:
            extract_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise ProjectError(f"Could not create uploaded project directory: {exc}") from exc

        with zipfile.ZipFile(BytesIO(data)) as archive:
            self._safe_extract(archive, extract_dir)

        source_dir = self._detect_source_root(extract_dir)
        target = self._discover_app_target(source_dir, app_target)
        session = self._launch_project(
            project_id=project_id,
            name=Path(filename).stem or f"project-{project_id}",
            source_dir=source_dir,
            app_target=target,
            project_dir=project_dir,
        )
        self._sessions[project_id] = session
        return session

    def call_project(
        self,
        project_id: str,
        *,
        method: str,
        path: str,
        headers: dict[str, str] | None,
        body: Any,
        raw_body: str | None,
    ) -> dict[str, Any]:
        session = self.get_project(project_id)
        if session.process.poll() is not None:
            raise ProjectError("Uploaded project server is not running")

        clean_path = self._clean_request_path(path)
        trace_id = uuid4().hex
        request_headers = {
            key: value
            for key, value in (headers or {}).items()
            if key.lower() not in {"host", "content-length", "x-trace-id"}
        }
        request_headers["X-Trace-Id"] = trace_id

        body_bytes: bytes | None = None
        if raw_body is not None:
            body_bytes = raw_body.encode("utf-8")
        elif body is not None:
            body_bytes = json.dumps(body).encode("utf-8")
            request_headers.setdefault("Content-Type", "application/json")

        response = self._request(
            f"{session.base_url}{clean_path}",
            method=method.upper(),
            headers=request_headers,
            body=body_bytes,
            allow_error=True,
        )
        trace = self.fetch_trace(project_id, trace_id)
        return {
            "trace_id": trace_id,
            "request": {
                "method": method.upper(),
                "path": clean_path,
            },
            "response": response,
            "trace": trace,
        }

    def fetch_trace(self, project_id: str, trace_id: str) -> dict[str, Any]:
        session = self.get_project(project_id)
        trace_url = f"{session.base_url}/__traceflow/traces/{trace_id}"
        last_error: Exception | None = None
        for _ in range(10):
            try:
                response = self._request(trace_url, method="GET")
                return response["json"]
            except Exception as exc:  # pragma: no cover - retry path is timing-sensitive
                last_error = exc
                time.sleep(0.08)
        raise ProjectError(f"Trace was not recorded: {last_error}")

    def list_traces(self, project_id: str) -> list[dict[str, Any]]:
        session = self.get_project(project_id)
        response = self._request(f"{session.base_url}/__traceflow/traces", method="GET")
        return response["json"] or []

    def latest_trace(self, project_id: str) -> dict[str, Any]:
        session = self.get_project(project_id)
        response = self._request(f"{session.base_url}/__traceflow/traces/latest", method="GET")
        return response["json"]

    def refresh_routes(self, project_id: str) -> list[dict[str, Any]]:
        session = self.get_project(project_id)
        response = self._request(f"{session.base_url}/__traceflow/routes", method="GET")
        session.routes = response["json"]
        return session.routes

    def _safe_extract(self, archive: zipfile.ZipFile, destination: Path) -> None:
        members = archive.infolist()
        if len(members) > MAX_ZIP_FILES:
            raise ProjectError("Zip contains too many files")

        destination = destination.resolve()
        for member in members:
            member_path = Path(member.filename)
            if member_path.is_absolute() or ".." in member_path.parts:
                raise ProjectError(f"Unsafe zip path rejected: {member.filename}")
            if member.is_dir():
                continue

            target = (destination / member_path).resolve()
            try:
                target.relative_to(destination)
            except ValueError as exc:
                raise ProjectError(f"Unsafe zip path rejected: {member.filename}") from exc

            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(member) as source, target.open("wb") as output:
                output.write(source.read())

    def _detect_source_root(self, extract_dir: Path) -> Path:
        children = [path for path in extract_dir.iterdir() if path.name != "__MACOSX"]
        directories = [path for path in children if path.is_dir()]
        files = [path for path in children if path.is_file()]
        if len(directories) == 1 and not any(file.suffix == ".py" for file in files):
            only_child = directories[0]
            package_like_names = {"api", "app", "application", "backend", "src"}
            if (only_child / "__init__.py").exists() or (
                only_child.name.lower() in package_like_names and (only_child / "main.py").exists()
            ):
                return extract_dir
            return only_child
        return extract_dir

    def _discover_app_target(self, source_dir: Path, preferred: str | None) -> str:
        if preferred:
            return self._normalize_preferred_target(source_dir, preferred.strip())

        candidates: list[str] = []
        for relative_file in ("app/main.py", "main.py", "src/main.py"):
            path = source_dir / relative_file
            if path.exists():
                module = self._module_path(source_dir, path)
                candidates.append(f"{module}:app")
                candidates.append(f"{module}:create_app()")

        for path in sorted(source_dir.rglob("*.py")):
            if self._should_skip(path):
                continue
            candidates.extend(self._targets_from_python_file(source_dir, path))

        unique_candidates = list(dict.fromkeys(candidates))
        if not unique_candidates:
            raise ProjectError(
                "Could not find a FastAPI app. Provide an app target like app.main:app."
            )
        return unique_candidates[0]

    def _normalize_preferred_target(self, source_dir: Path, target: str) -> str:
        if ":" not in target:
            return target

        module_name, app_name = target.split(":", 1)
        if "." in module_name:
            return target

        direct_module = source_dir / f"{module_name}.py"
        if direct_module.exists():
            return target

        for package_dir in sorted(path for path in source_dir.iterdir() if path.is_dir()):
            packaged_module = package_dir / f"{module_name}.py"
            if (package_dir / "__init__.py").exists() and packaged_module.exists():
                return f"{package_dir.name}.{module_name}:{app_name}"

        return target

    def _targets_from_python_file(self, source_dir: Path, path: Path) -> list[str]:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:
            return []

        module = self._module_path(source_dir, path)
        targets: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.Assign, ast.AnnAssign)) and self._is_fastapi_assignment(node):
                for target_name in self._assignment_names(node):
                    targets.append(f"{module}:{target_name}")
            elif isinstance(node, ast.FunctionDef) and node.name in {"create_app", "get_app"}:
                targets.append(f"{module}:{node.name}()")
        return targets

    def _is_fastapi_assignment(self, node: ast.Assign | ast.AnnAssign) -> bool:
        value = node.value
        if isinstance(value, ast.Call):
            func = value.func
            if isinstance(func, ast.Name) and func.id == "FastAPI":
                return True
            if isinstance(func, ast.Attribute) and func.attr == "FastAPI":
                return True
            if isinstance(func, ast.Name) and func.id in {"create_app", "get_app"}:
                return True
        return False

    def _assignment_names(self, node: ast.Assign | ast.AnnAssign) -> list[str]:
        raw_targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        names: list[str] = []
        for target in raw_targets:
            if isinstance(target, ast.Name):
                names.append(target.id)
        return names

    def _module_path(self, source_dir: Path, path: Path) -> str:
        relative = path.relative_to(source_dir).with_suffix("")
        parts = list(relative.parts)
        if parts[-1] == "__init__":
            parts = parts[:-1]
        return ".".join(parts)

    def _launch_project(
        self,
        *,
        project_id: str,
        name: str,
        source_dir: Path,
        app_target: str,
        project_dir: Path,
    ) -> ProjectSession:
        port = self._find_free_port()
        log_path = project_dir / "runtime.log"
        env = os.environ.copy()
        env["TRACEFLOW_TARGET_APP"] = app_target
        env["TRACEFLOW_PROJECT_ROOT"] = str(source_dir)
        env["TRACEFLOW_PROFILE_ROOTS"] = str(source_dir)
        env["PYTHONPATH"] = os.pathsep.join(
            item
            for item in [
                str(TRACEFLOW_ROOT),
                str(source_dir),
                env.get("PYTHONPATH", ""),
            ]
            if item
        )

        command = [
            sys.executable,
            "-m",
            "uvicorn",
            "traceflow.runtime:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--log-level",
            "warning",
        ]

        with log_path.open("wb") as log_file:
            process = subprocess.Popen(
                command,
                cwd=source_dir,
                env=env,
                stdout=log_file,
                stderr=subprocess.STDOUT,
            )

        session = ProjectSession(
            project_id=project_id,
            name=name,
            source_dir=source_dir,
            app_target=app_target,
            port=port,
            process=process,
            log_path=log_path,
            routes=[],
        )

        try:
            self._wait_for_health(session)
            session.routes = self.refresh_routes(project_id) if project_id in self._sessions else self._runtime_routes(session)
        except Exception as exc:
            process.terminate()
            time.sleep(0.2)
            raise ProjectError(
                f"Could not launch FastAPI app target '{app_target}'. {exc}\n{session.read_log_tail()}"
            ) from exc

        return session

    def _wait_for_health(self, session: ProjectSession) -> None:
        url = f"{session.base_url}/__traceflow/health"
        last_error: Exception | None = None
        for _ in range(50):
            if session.process.poll() is not None:
                raise ProjectError(f"Process exited early.\n{session.read_log_tail()}")
            try:
                self._request(url, method="GET")
                return
            except Exception as exc:
                last_error = exc
                time.sleep(0.1)
        raise ProjectError(f"Health check timed out: {last_error}")

    def _runtime_routes(self, session: ProjectSession) -> list[dict[str, Any]]:
        response = self._request(f"{session.base_url}/__traceflow/routes", method="GET")
        return response["json"]

    def _request(
        self,
        url: str,
        *,
        method: str,
        headers: dict[str, str] | None = None,
        body: bytes | None = None,
        allow_error: bool = False,
    ) -> dict[str, Any]:
        request = urllib.request.Request(
            url,
            data=body,
            headers=headers or {},
            method=method,
        )
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                return self._response_payload(response.status, dict(response.headers), response.read())
        except urllib.error.HTTPError as exc:
            payload = self._response_payload(exc.code, dict(exc.headers), exc.read())
            if allow_error:
                return payload
            raise

    def _response_payload(
        self,
        status_code: int,
        headers: dict[str, str],
        body: bytes,
    ) -> dict[str, Any]:
        text = body.decode("utf-8", errors="replace")
        parsed: Any = None
        content_type = headers.get("Content-Type") or headers.get("content-type") or ""
        if "application/json" in content_type and text:
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError:
                parsed = None
        return {
            "status_code": status_code,
            "headers": headers,
            "body": text,
            "json": parsed,
        }

    def _clean_request_path(self, path: str) -> str:
        clean_path = path.strip() or "/"
        if not clean_path.startswith("/"):
            clean_path = f"/{clean_path}"
        if clean_path.startswith("/__traceflow"):
            raise ProjectError("Internal TraceFlow paths cannot be called from the simulator")
        return clean_path

    def _should_skip(self, path: Path) -> bool:
        return any(part in SKIPPED_DIRS for part in path.parts)

    def _find_free_port(self) -> int:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", 0))
            return int(sock.getsockname()[1])


project_manager = ProjectManager()
