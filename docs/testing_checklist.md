# Testing Checklist

Use this checklist when validating changes in this repository.

## Core Execution
- `python3 jarvis.py talk "test"` works.
- The project executes without runtime errors for the modified flow.
- `python3 jarvis.py log "test"` works.
- `python3 jarvis.py remind "test" "2026-04-10 09:00"` works.
- `python3 jarvis.py search "test"` works.
- `python3 jarvis.py today` works.
- `python3 jarvis.py context` works.
- `uvicorn app.main:app --host 127.0.0.1 --port 8000` starts for the web flow.
- `GET /health` returns success for the web flow.
- `GET /api/overview` returns the expected web payload keys.
- `GET /api/search?q=<term>` returns entries from active and archived logs when applicable.
- `POST /api/prompt` supports at least `log`, `remind`, `search`, `today`, and `context` prompt patterns.

## Input Compatibility
- Existing inputs remain compatible.
- Persisted files remain readable after changes.
- `WORKING_CONTEXT.md` remains readable and user note sections survive refreshes.
- Files under `memory/` remain synchronized with the root persisted files.
- Date formats remain consistent with the documented contract.
- Web API base URL setting in the frontend can be saved and reused in the browser.
- Archived files under `archives/` remain readable and keep the same line layout as active logs.

## Output Stability
- Outputs did not change unexpectedly.
- Report layouts were preserved.
- Column names, field names, and ordering remain consistent where applicable.
- Types of persisted data remain consistent.
- `talk` creates both the conversation file and the summary file with the documented layout.
- The web dashboard remains usable on mobile-width screens.
- The web dashboard remains usable with a single-prompt interaction model (no action buttons required).
- Prompt submissions should appear in history with corresponding assistant responses.
- Read-only flows (`search`, `today`, `context`, `GET /api/context`, `GET /api/overview`) should not trigger unintended rewrites in persisted files.

## Documentation Consistency
- Business rule changes were reflected in `docs/business_rules.md`.
- Data contract changes were reflected in `docs/data_contracts.md`.
- Layout changes were reflected in `docs/report_layouts.md`.
- Validation expectations still match this checklist.

## Regression Awareness
- Existing scripts still run.
- Existing tests, if present later, continue passing.
- New assumptions were documented instead of silently encoded.
