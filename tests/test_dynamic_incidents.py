from __future__ import annotations

from pathlib import Path

import pytest

from eval.runner import run_fixture


INCIDENT_FIXTURES = sorted((Path(__file__).parents[1] / "eval" / "incidents").glob("*.json"))


@pytest.mark.parametrize("fixture_path", INCIDENT_FIXTURES, ids=[path.stem for path in INCIDENT_FIXTURES])
def test_incident_fixture_classifies_expected_category(fixture_path: Path) -> None:
    result = run_fixture(fixture_path)

    assert result["actual_category"] == result["expected_category"], result
    assert result["top_statement"]
