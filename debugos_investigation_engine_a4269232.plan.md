---
name: DebugOS Investigation Engine
overview: Rebuild DebugOS as an investigation agent loop with a clean separation between deterministic machinery (parsing, redaction, citation verification, scoring) and LLM reasoning (hypothesis generation, evidence interpretation). Phase 1 is a runnable, demoable vertical slice over logs + stack traces; later phases add code intelligence, temporal reasoning, and learning.
todos:
  - id: scaffold
    content: "Phase 0: scaffold FastAPI/SQLAlchemy project, config, cached schema-constrained OpenAI client wrapper"
    status: pending
  - id: eval
    content: "Phase 0: build eval harness + 8-12 labeled log/stack-trace incident fixtures with known root cause and category"
    status: pending
  - id: ingestion
    content: "Phase 1: implement log normalizer, stack-trace parser, secret/PII redaction, and fingerprinting/dedup into normalized evidence records with provenance spans"
    status: pending
  - id: store
    content: "Phase 1: implement append-only evidence store + token-budgeted ranked retrieval"
    status: pending
  - id: hypotheses
    content: "Phase 1: LLM hypothesis generation with forced category diversity and de-duplication"
    status: pending
  - id: link-verify
    content: "Phase 1: LLM evidence-to-hypothesis linking + deterministic citation verifier that drops unverifiable signals"
    status: pending
  - id: scoring
    content: "Phase 1: implement deterministic evidence-score rubric (strength weights, independence cap, saturating normalization, discriminating power)"
    status: pending
  - id: orchestrator
    content: "Phase 1: implement Investigation Orchestrator state machine with step budget, decision rules, evidence requests, and Unknown path"
    status: pending
  - id: report-ui
    content: "Phase 1: report generator (ranked grounded causes + next steps) + demo UI + feedback capture"
    status: pending
  - id: phase2-code
    content: "Phase 2: source-code retrieval (symbol resolution, snippet, git blame), failure pattern library, novelty score with arbitration policy"
    status: pending
isProject: false
---

# DebugOS: Investigation Engine (corrected architecture + phased plan)

## Core architectural corrections (vs. the original spec)

- Replace the linear 15-component pipeline with a single **Investigation Orchestrator** (state machine) that loops `ASSESS -> HYPOTHESIZE -> RETRIEVE -> LINK -> VERIFY -> SCORE -> DECIDE`, with explicit step budget and termination rules.
- Split work into two strict tiers:
  - **Deterministic (code):** parsing, secret redaction, fingerprinting/dedup, evidence retrieval/ranking, citation verification, score aggregation, termination logic.
  - **Probabilistic (LLM):** hypothesis generation (category-diverse), evidence-to-hypothesis linking, evidence-request authoring, report prose.
- Make **Evidence Score** a deterministic, auditable rubric over *verified* signals - never an LLM-emitted number. The LLM proposes links and a relation/strength label; code computes the score.
- Add a **Citation Verifier**: every supporting/contradicting signal must resolve to a real `(artifact_id, span)`; unverifiable signals are dropped. This is the anti-hallucination backbone.
- Add **secret/PII redaction at ingestion** before any text reaches the LLM.
- Build an **eval harness + labeled sample incidents from day one** so accuracy metrics are measurable.
- Defer Timeline, State-Transition, Code Intelligence (full), and Learning Graph; scope each down realistically (see phases). Add an explicit arbitration policy between Failure-Pattern matching and Novelty so learning never overrides fresh evidence.

## Data model (SQLite dev, Postgres-compatible)

- `investigation(id, status, created_at, step_count, budget, summary)` - status in {in_progress, ranked, complete, evidence_insufficient, unknown}.
- `artifact(id, investigation_id, type, raw_text, redaction_map, source_meta)` - append-only; raw retained for provenance.
- `evidence(id, investigation_id, artifact_id, type, span_start, span_end, normalized_text, signal_tags, fingerprint, embedding)` - never discarded; `fingerprint` enables dedup/clustering.
- `hypothesis(id, investigation_id, category, statement, novelty_score, evidence_score, status)` - category in {CODE, CONFIGURATION, DATA, BUSINESS_LOGIC, INFRASTRUCTURE, DEPENDENCY, NETWORK, SECURITY, EXTERNAL_SERVICE}.
- `evidence_link(id, hypothesis_id, evidence_id, relation, strength, verified, rationale)` - relation in {supports, contradicts}; `verified` set by Citation Verifier.
- `evidence_request(id, investigation_id, hypothesis_id, what, why, expected_signal, format)`.
- `feedback(investigation_id, chosen_root_cause, was_correct, resolution_note)` - feeds the eval dataset.

## Scoring rubric (deterministic, reproducible)

For each hypothesis H, over its `verified` links only:
- `strength` weights: weak=1, moderate=2, strong=3.
- Independence cap: contributions from the same `artifact_id` + `signal_tag` are capped (prevents one repeated log line from dominating).
- `raw = sum(supporting strengths, capped) - sum(contradicting strengths)`.
- `evidence_score = round(10 * (1 - exp(-raw / k)))` saturating to 0-10 (k tuned on eval set).
- Also compute **discriminating power**: how much the evidence separates H from the runner-up (drives evidence requests).
- Report the signal breakdown, never a single confidence percentage.

## Decision / termination rules (deterministic)

- **Complete:** top `evidence_score >= T_high` AND margin over #2 `>= M`.
- **Ranked + request evidence:** several hypotheses close together AND a discriminating signal is identifiable (emit `evidence_request`s ordered by expected information gain).
- **Unknown:** top `evidence_score < T_low` and no informative evidence obtainable.
- **Budget stop:** `step_count >= budget` -> emit best-effort ranked result labeled accordingly.

## Tech stack

- Python 3.11, **FastAPI** (REST), **SQLAlchemy** + SQLite (Postgres-ready), **OpenAI** SDK.
- Model tiering: cheap model for parsing/classification/redaction-assist; strong reasoning model for hypothesis + linking. Cache LLM calls by input hash.
- Demo UI: lightweight (FastAPI + server-rendered HTML/htmx, or Streamlit) to paste logs/stack traces and watch the investigation loop, ranked hypotheses, grounded evidence, and evidence requests.

## Phasing (derisked ordering)

### Phase 0 - Foundations
- Repo scaffold (`app/`, `tests/`, `eval/`), config, OpenAI client wrapper with caching + JSON-schema-constrained outputs.
- Eval harness + 8-12 labeled sample incidents (log + stack-trace bundles with known root cause/category).

### Phase 1 - Runnable demo (Logs + Stack Traces)
- Ingestion: log normalizer (timestamp parsing, multi-line stack-trace stitching), stack-trace parser (frame -> file:line:symbol), **secret/PII redaction**, fingerprinting/dedup.
- Evidence store + token-budgeted ranked retrieval.
- Orchestrator loop with category-diverse hypothesis generation, evidence linking, **citation verification**, deterministic scoring, decision rules, evidence requests, and the Unknown path.
- Report generator (ranked causes, grounded evidence, impact, recommended next step) + demo UI + feedback capture.

### Phase 2 - Source + priors
- Source-code retrieval scoped to: stack-frame symbol resolution, surrounding code snippet, `git blame` of the failing line.
- Failure Pattern Library (seeded patterns) + Novelty score, with arbitration so priors never override stronger fresh evidence.

### Phase 3 - Temporal + more inputs (needs correlation IDs)
- Config files, HAR, OTel traces ingestion; Timeline Engine and State-Transition Engine gated on availability of trace/request IDs.

### Phase 4 - Learning + suggestions
- Learning Graph over resolved investigations (incident <-> evidence <-> root cause <-> resolution), historical retrieval feeding (not dictating) hypotheses; patch suggestions; automated validation.

## Key files (Phase 0-1)

- `app/main.py` - FastAPI app + routes (`/investigations`, `/investigations/{id}/evidence`, `/investigations/{id}/step`, `/investigations/{id}/report`).
- `app/orchestrator.py` - the investigation state machine.
- `app/ingestion/` - `logs.py`, `stack_traces.py`, `redaction.py`, `fingerprint.py`.
- `app/evidence/store.py`, `app/evidence/retrieval.py`.
- `app/reasoning/hypotheses.py`, `app/reasoning/linking.py`, `app/reasoning/requests.py` (LLM, schema-constrained).
- `app/scoring.py`, `app/verifier.py` - deterministic scoring + citation verification.
- `app/report.py`, `app/models.py`, `app/llm.py` (cached client).
- `eval/runner.py` + `eval/incidents/*` - accuracy harness and labeled fixtures.