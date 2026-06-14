from __future__ import annotations

import io
import zipfile
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from traceflow.app import create_app
from traceflow.projects.manager import ProjectError, parse_github_repo


@pytest.mark.parametrize(
    ("repo", "owner", "name", "ref"),
    [
        ("https://github.com/octo/repo", "octo", "repo", None),
        ("https://github.com/octo/repo.git", "octo", "repo", None),
        ("https://github.com/octo/repo/tree/develop", "octo", "repo", "develop"),
        ("octo/repo", "octo", "repo", None),
        ("octo/repo.git", "octo", "repo", None),
        ("github.com/octo/repo/tree/feature/x", "octo", "repo", "feature/x"),
    ],
)
def test_parse_github_repo(repo: str, owner: str, name: str, ref: str | None) -> None:
    assert parse_github_repo(repo) == (owner, name, ref)


def test_parse_github_repo_rejects_invalid_input() -> None:
    with pytest.raises(ProjectError, match="owner/repo"):
        parse_github_repo("not-a-repo")


def _sample_zip_bytes() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("demo-app/main.py", "print('hello')\n")
    return buffer.getvalue()


def test_connect_github_validation_returns_400() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/projects/connect-github",
        json={"repo": "invalid-repo-string"},
    )

    assert response.status_code == 400
    assert "owner/repo" in response.json()["detail"]


def test_connect_github_success_with_monkeypatched_download() -> None:
    client = TestClient(create_app())
    zip_bytes = _sample_zip_bytes()

    with patch(
        "traceflow.projects.manager.ProjectManager._download_github_zipball",
        return_value=zip_bytes,
    ), patch(
        "traceflow.projects.manager.ProjectManager._launch_project",
    ) as launch_mock:
        from traceflow.projects.manager import ProjectSession

        launch_mock.return_value = ProjectSession(
            project_id="abc123",
            name="octo-repo",
            source_dir=__import__("pathlib").Path("/tmp/source"),
            app_target="main:app",
            port=8765,
            process=__import__("subprocess").Popen(
                [__import__("sys").executable, "-c", "import time; time.sleep(60)"],
                stdout=__import__("subprocess").DEVNULL,
                stderr=__import__("subprocess").DEVNULL,
            ),
            log_path=__import__("pathlib").Path("/tmp/log.txt"),
            routes=[{"method": "GET", "path": "/"}],
        )

        response = client.post(
            "/api/projects/connect-github",
            json={"repo": "octo/repo", "ref": "main"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["name"] == "octo-repo"
    assert payload["project_id"] == "abc123"
