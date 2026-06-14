# DebugOS Investigation Engine

Standalone DebugOS module extracted from the merged codebase.

## Run

```powershell
cd debug
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn debug_module.main:app --reload
```

Open http://127.0.0.1:8000.

## Test and evaluate

```powershell
pytest
$env:ENABLE_LLM_REASONING='false'; python -m eval.runner
$env:ENABLE_LLM_REASONING='true'; python -m eval.runner
```
