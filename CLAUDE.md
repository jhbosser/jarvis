# CLAUDE.md

## Project Overview
This project is a Python local assistant focused on automation, lightweight data processing, reminder management, and generation of console-friendly outputs from structured local files. The main persistence layer is file-based and must remain stable.

Always read `PROJECT_CONTEXT.md` before modifying code.

## Main Scripts
- `jarvis.py`: main CLI for `log`, `remind`, `search`, and `today`.
- `reminder_service.py`: polling service that completes due reminders and triggers notifications.
- `utils.py`: file handling, parsing, normalization, search, and memory map maintenance.

## Execution Commands
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 jarvis.py log "Example note"
python3 jarvis.py remind "Example reminder" "2026-04-10 09:00"
python3 jarvis.py search "Example"
python3 jarvis.py today
python3 reminder_service.py
```

## Development Constraints
- Always read `PROJECT_CONTEXT.md` before changing implementation.
- Verify data contracts in `docs/data_contracts.md`.
- Verify layouts in `docs/report_layouts.md`.
- Do not infer fiscal rules.
- Preserve structure of generated files.
- Prefer small, localized changes.
- Do not remove existing logic unless the change is explicitly requested and justified.

## Data Safety Rules
- Treat `memory_log.md`, `memory_map.md`, and `reminders.json` as authoritative persisted data.
- Do not modify user data manually unless the task explicitly requires it.
- Do not modify data in any source database.
- Scripts must not alter source-system records.
- Use fictitious data in examples and documentation.

## Validation Steps
- Validate changes using `docs/testing_checklist.md`.
- Confirm CLI commands still execute without error.
- Confirm new and existing inputs remain compatible with documented contracts.
- Confirm outputs and layouts remain unchanged unless intentionally updated and documented.
- Confirm reminder persistence and log persistence remain readable after changes.
