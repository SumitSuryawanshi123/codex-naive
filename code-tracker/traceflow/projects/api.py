from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from .manager import ProjectError, project_manager


router = APIRouter(prefix="/projects", tags=["projects"])


class ProjectRequest(BaseModel):
    method: str = Field(default="GET", pattern="^(GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD)$")
    path: str = "/"
    headers: dict[str, str] = Field(default_factory=dict)
    body: Any = None
    raw_body: str | None = None


class GithubConnectRequest(BaseModel):
    repo: str
    ref: str | None = None
    token: str | None = None
    app_target: str | None = None


@router.get("")
async def list_projects() -> list[dict[str, Any]]:
    return project_manager.list_projects()


@router.post("/upload")
async def upload_project(request: Request) -> dict[str, Any]:
    filename = request.headers.get("x-project-filename", "project.zip")
    app_target = request.headers.get("x-app-target") or None
    data = await request.body()
    try:
        session = project_manager.upload_zip(
            filename=filename,
            data=data,
            app_target=app_target,
        )
        return session.to_dict()
    except ProjectError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/connect-github")
async def connect_github_project(payload: GithubConnectRequest) -> dict[str, Any]:
    try:
        session = project_manager.connect_github(
            repo=payload.repo,
            ref=payload.ref,
            token=payload.token,
            app_target=payload.app_target,
        )
        return session.to_dict()
    except ProjectError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{project_id}")
async def get_project(project_id: str) -> dict[str, Any]:
    try:
        return project_manager.get_project(project_id).to_dict()
    except ProjectError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/{project_id}")
async def stop_project(project_id: str) -> dict[str, Any]:
    try:
        return project_manager.stop_project(project_id)
    except ProjectError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{project_id}/routes")
async def get_project_routes(project_id: str) -> list[dict[str, Any]]:
    try:
        return project_manager.refresh_routes(project_id)
    except ProjectError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{project_id}/request")
async def call_project(project_id: str, request: ProjectRequest) -> dict[str, Any]:
    try:
        return project_manager.call_project(
            project_id,
            method=request.method,
            path=request.path,
            headers=request.headers,
            body=request.body,
            raw_body=request.raw_body,
        )
    except ProjectError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{project_id}/traces")
async def list_project_traces(project_id: str) -> list[dict[str, Any]]:
    try:
        return project_manager.list_traces(project_id)
    except ProjectError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{project_id}/traces/latest")
async def get_latest_project_trace(project_id: str) -> dict[str, Any]:
    try:
        return project_manager.latest_trace(project_id)
    except ProjectError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{project_id}/traces/{trace_id}")
async def get_project_trace(project_id: str, trace_id: str) -> dict[str, Any]:
    try:
        return project_manager.fetch_trace(project_id, trace_id)
    except ProjectError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
