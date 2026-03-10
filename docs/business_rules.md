# Business Rules

This document records the business and operational rules that AI agents and developers must preserve when working on this repository.

## Current Rules
- Every new event must be appended to `memory_log.md` with a timestamp.
- `memory_log.md` may be automatically rotated into `archives/` to keep the active file lightweight.
- Historical continuity must be preserved across `memory_log.md` and `archives/memory_log_*.md`.
- Every new logged event must refresh `memory_map.md`.
- Reminders must be persisted in `reminders.json`.
- The reusable working context must be persisted in `WORKING_CONTEXT.md`.
- Every `talk` command must generate a timestamped file in `conversations/`.
- Every `talk` command must generate a structured summary file in `summaries/`.
- The project must keep spec-aligned derived files in `memory/` synchronized with the root persisted files.
- Reminder status values currently used by the project are `pending` and `completed`.
- Log entry format is `YYYY-MM-DD HH:MM - category - description`.
- Reminder datetime format is `YYYY-MM-DD HH:MM`.
- Automatic sections in `WORKING_CONTEXT.md` must refresh when logs or reminders change.
- `memory/active_context.md` and `memory/pending_items.md` are derived artifacts and must be refreshable from local persisted state.
- Automatic sections in `WORKING_CONTEXT.md` may contain explicit inferences derived from local records.
- User note sections in `WORKING_CONTEXT.md` must not be overwritten by automatic refreshes.
- Existing persisted file formats must remain backward compatible.
- Read-only commands and endpoints should not rewrite persisted files unless a refresh is explicitly required.
- The web API must reuse the existing persistence flow instead of introducing silent parallel storage.
- The first web interface must remain responsive for mobile browsers while preserving the same behaviors as the CLI flows it exposes.
- The first web layer may expose permissive CORS for local prototyping, but production restrictions must be reviewed before public deployment.

## Rules That Must Be Registered Here
- Calculation rules
- Operational exceptions
- Rounding criteria
- Business assumptions
- Important project decisions

## Change Policy
- Any change to critical behavior must be reflected here in the same task.
- Do not infer fiscal, accounting, or financial rules.
- If a rule is uncertain, document it as an open assumption instead of implementing speculation.
