from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any

from debug_module.config import get_settings


class CachedLLMClient:
    def __init__(self) -> None:
        settings = get_settings()
        self.model = settings.openai_model
        self.api_key = settings.openai_api_key
        self.cache_path: Path | None = Path(settings.llm_cache_path)
        try:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(self.cache_path) as conn:
                conn.execute("create table if not exists cache (key text primary key, value text not null)")
        except OSError:
            self.cache_path = None

    def _key(self, task: str, payload: dict[str, Any], schema: dict[str, Any] | None) -> str:
        blob = json.dumps({"task": task, "payload": payload, "schema": schema, "model": self.model}, sort_keys=True)
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()

    def complete_json(self, task: str, payload: dict[str, Any], schema: dict[str, Any] | None = None) -> dict[str, Any] | None:
        key = self._key(task, payload, schema)
        if self.cache_path:
            with sqlite3.connect(self.cache_path) as conn:
                row = conn.execute("select value from cache where key = ?", (key,)).fetchone()
                if row:
                    return json.loads(row[0])
        if not self.api_key:
            return None
        try:
            from openai import OpenAI

            client = OpenAI(api_key=self.api_key)
            response = client.responses.create(
                model=self.model,
                input=[
                    {"role": "system", "content": "Return compact JSON only."},
                    {"role": "user", "content": json.dumps({"task": task, "payload": payload})},
                ],
                text={"format": {"type": "json_schema", "name": task, "schema": schema or {"type": "object"}}},
            )
            parsed = json.loads(response.output_text)
        except Exception:
            return None
        if self.cache_path:
            with sqlite3.connect(self.cache_path) as conn:
                conn.execute("insert or replace into cache(key, value) values(?, ?)", (key, json.dumps(parsed)))
        return parsed
