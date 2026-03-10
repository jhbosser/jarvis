# Data Contracts

This document describes the expected data structures used by the current project. Any contract change must be documented here before or together with the code change.

## Expected Files

### `memory_log.md`
- Purpose: active chronological log window of user events.
- Record format: one line per event.
- Pattern: `YYYY-MM-DD HH:MM - category - description`
- Required fields:
  - timestamp
  - category
  - description
- Data types:
  - timestamp: datetime string
  - category: string
  - description: string
- Date format: `YYYY-MM-DD HH:MM`
- Schema validation:
  - lines should contain three logical segments separated by ` - `
  - new writes should append to active records

### `archives/memory_log_*.md`
- Purpose: archived historical slices rotated from the active `memory_log.md`.
- Record format: same as `memory_log.md`.
- Filename pattern: `memory_log_YYYYMMDD_HHMMSS_microseconds.md`
- Schema validation:
  - lines should preserve `YYYY-MM-DD HH:MM - category - description`
  - archived files should not be rewritten after creation
  - full timeline is represented by active + archived log files

### `memory_map.md`
- Purpose: aggregated entity summary derived from logged events.
- Record format: blocks separated by blank lines.
- Expected fields in each block:
  - entity name on first line
  - `type: <string>`
  - `mentions: <integer>`
  - `last_event: <string>`
- Required fields:
  - entity identifier
  - type
  - mentions
  - last_event
- Data types:
  - entity identifier: string
  - type: string
  - mentions: integer
  - last_event: string
- Schema validation:
  - each entity block should contain the four expected lines
  - `mentions` should remain numeric

### `memory/memory_log.md`
- Purpose: spec-aligned mirror of the root `memory_log.md`.
- Record format: same as `memory_log.md`.
- Schema validation:
  - content should remain synchronized with the active root log file

### `memory/memory_map.md`
- Purpose: spec-aligned mirror of the root `memory_map.md`.
- Record format: same as `memory_map.md`.
- Schema validation:
  - content should remain synchronized with the root memory map

### `memory/pending_items.md`
- Purpose: derived list of open reminders for the context engine structure.
- Record format: one markdown bullet per pending item.
- Pattern: `- <title> | <datetime>`
- Fallback format when empty: `- None`

### `memory/active_context.md`
- Purpose: spec-aligned active context snapshot for the next conversation.
- Record format: plain text sections.
- Expected sections:
  - `Recent entities`
  - `Active pending items`
  - `Recent topics`
  - `Recent decisions`
- Schema validation:
  - sections should remain readable as plain text
  - pending items should be derived from `reminders.json`

### `reminders.json`
- Purpose: persisted reminders and completion state.
- Structure: JSON array of reminder objects.
- Expected fields:
  - `id`
  - `title`
  - `datetime`
  - `status`
  - `completed_at` when applicable
- Required fields for pending reminders:
  - `id`
  - `title`
  - `datetime`
  - `status`
- Data types:
  - `id`: string
  - `title`: string
  - `datetime`: datetime string
  - `status`: string
  - `completed_at`: datetime string, optional
- Date format: `YYYY-MM-DD HH:MM`
- Schema validation:
  - file must remain valid JSON
  - root element must remain a list
  - reminder status should remain compatible with current flows

### `conversations/*.md`
- Purpose: timestamped conversation capture files created by `talk`.
- Filename pattern: `YYYY-MM-DD_HHMM.md`
- Required fields:
  - `timestamp: <YYYY-MM-DD HH:MM>`
  - `user input: <text>`
  - `assistant response: <text>`
- Schema validation:
  - file must remain readable as plain text markdown-like text
  - filenames must preserve timestamp format

### `summaries/*_context.md`
- Purpose: structured summary created after each `talk`.
- Filename pattern: `YYYY-MM-DD_HHMM_context.md`
- Expected sections:
  - `Date: <YYYY-MM-DD>`
  - `Facts`
  - `Entities`
  - `Pending items`
  - `Decisions`
  - `Summary`
- Schema validation:
  - section order should remain stable
  - output should remain plain text and inspectable

### `WORKING_CONTEXT.md`
- Purpose: reusable context snapshot for future chats, combining agent-maintained automatic context and preserved user notes.
- Record format: markdown document with fixed top-level sections.
- Expected sections:
  - `## Automatic Context`
  - `### Last updated`
  - `### Current focus`
  - `### Active items`
  - `### Recent facts`
  - `### Relevant entities`
  - `### Open threads`
  - `## User Notes`
  - `### Stable preferences`
  - `### Personal context`
- Required behaviors:
  - automatic sections may be rewritten by the application
  - automatic sections may include explicit inferences derived from stored data
  - user note sections remain editable and preserved
- Data types:
  - markdown headings: string
  - bullet entries under automatic sections: string
- Schema validation:
  - file must remain readable as plain text markdown
  - automatic section headings must remain stable for refresh logic

## Spreadsheet / CSV Contracts
- The current repository does not ship spreadsheet ingestion or CSV-based production pipelines.
- If future work introduces files, worksheets, column names, mandatory fields, or typed schemas, they must be documented here before agents change them.

## HTTP API Contracts

### `GET /health`
- Purpose: lightweight service health check.
- Response shape:
  - `status`: string

### `GET /api/overview`
- Purpose: web dashboard bootstrap payload.
- Response shape:
  - `today_logs`: list of strings
  - `recent_logs`: list of strings
  - `pending_reminders`: list of reminder objects compatible with `reminders.json`
  - `working_context`: string

### `GET /api/today`
- Purpose: fetch today's log entries for the web interface.
- Response shape:
  - `entries`: list of strings
- Notes:
  - entries may include same-day records from archived slices when rotation occurred

### `GET /api/context`
- Purpose: fetch the current working context snapshot.
- Response shape:
  - `content`: string

### `GET /api/search`
- Purpose: search logs (active + archives) and memory map using the current keyword matching behavior.
- Query parameters:
  - `q`: string, required
- Response shape:
  - `query`: string
  - `logs`: list of strings
  - `memory_map`: list of strings

### `GET /api/reminders`
- Purpose: list reminder records for the web interface.
- Response shape:
  - `items`: list of reminder objects compatible with `reminders.json`

### `POST /api/log`
- Purpose: create a new log entry through the web interface.
- Request shape:
  - `text`: string
- Response shape:
  - `entry`: string

### `POST /api/talk`
- Purpose: capture a conversation turn through HTTP.
- Request shape:
  - `text`: string
  - `assistant_response`: string, optional
- Response shape:
  - `assistant_response`: string
  - `conversation_path`: string
  - `summary_path`: string

### `POST /api/reminders`
- Purpose: create a reminder through the web interface.
- Request shape:
  - `title`: string
  - `datetime`: string in `YYYY-MM-DD HH:MM`
- Response shape:
  - reminder object compatible with `reminders.json`

### `POST /api/reminders/{id}/complete`
- Purpose: mark a reminder as completed through the web interface.
- Path parameters:
  - `id`: string
- Response shape:
  - reminder object compatible with `reminders.json`

## Preservation Rules
- Preserve file compatibility with existing user data.
- Do not rename fields or change date formats without explicit instruction.
- Do not change column names, expected worksheet names, or output contracts without documenting the change here first.
