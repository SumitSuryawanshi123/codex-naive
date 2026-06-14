from __future__ import annotations

import pytest

from debug_module.config import get_settings


@pytest.fixture(autouse=True)
def disable_external_llm_calls(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("ENABLE_LLM_REASONING", "false")
    get_settings.cache_clear()
    try:
        yield
    finally:
        get_settings.cache_clear()
