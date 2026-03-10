# PROJECT_CONTEXT.md

## Project Purpose
Jarvis is a local-first Python assistant that stores user memory and reminders in plain text and JSON files. It supports operational automation around capturing notes, tracking reminders, searching historical information, and presenting simple report-like console outputs.

## Business Context
The repository acts as an external memory layer. Its priority is reliability, auditability, and simplicity rather than complex infrastructure. Because the project stores user-generated records, stability of file formats and predictability of outputs matter more than feature expansion.

Critical rules and operational decisions must be documented in `docs/business_rules.md`.

## Data Sources
- Direct CLI input from the user via `jarvis.py`.
- Existing local files:
  - `memory_log.md`
  - `memory_map.md`
  - `reminders.json`
  - `WORKING_CONTEXT.md`
- Internal parsing and entity extraction implemented in `utils.py`.

## Data Flow
1. User runs a CLI command.
2. Input is parsed and normalized.
3. The project persists data to local files.
4. Memory aggregates are updated when a log is written.
5. The working context snapshot is refreshed when logs or reminders change.
6. Search and daily listing commands read local persisted files.
7. The reminder service polls pending reminders and marks due items as completed.

## Outputs
- Plain text log entries in `memory_log.md`.
- Aggregated entity summaries in `memory_map.md`.
- JSON reminders in `reminders.json`.
- Reusable cross-chat context snapshot in `WORKING_CONTEXT.md`.
- Console tables and status messages from CLI commands.
- Desktop reminder notifications from `reminder_service.py`.

Report and output layouts must be registered in `docs/report_layouts.md`.

## Critical Business Rules
- Logged events must remain append-only and timestamped.
- Writing a log entry must refresh the memory map consistently.
- Reminder records must preserve status values and scheduled datetime format.
- The working context file must preserve user note sections while automatic context sections stay refreshable.
- File-based compatibility is more important than internal refactoring.

Critical business rules must also be maintained in `docs/business_rules.md`.

## Known Limitations
- No formal automated test suite is present today.
- Data contracts are lightweight and inferred from current local files.
- Search depends on simple keyword matching and entity extraction heuristics.
- Notification delivery depends on the local environment supporting `plyer`.
- There is no source database in the current implementation, but future agents must still avoid introducing scripts that modify source-system data.

## Important Assumptions
- The repository is used locally by a single operator or a small trusted workflow.
- Persisted files are the primary source of truth.
- Existing formats must remain backward compatible.
- Agents should not infer new business, fiscal, accounting, or financial rules from partial context.

Data contracts must be maintained in `docs/data_contracts.md`.
