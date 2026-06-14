from app.ingestion.logs import ingest_text


def test_redacts_and_extracts_stack_trace() -> None:
    raw = "2026-06-14T01:00:00Z ERROR token=supersecret123 exception\n  File \"app/main.py\", line 12, in handler\n"
    redacted, redaction_map, candidates = ingest_text(raw)
    assert "supersecret123" not in redacted
    assert redaction_map
    assert candidates[0].type == "stack_trace"
    assert "stack_frame" in candidates[0].signal_tags
