# Jarvis Behavior Guide

Jarvis is a local-first personal assistant used as external memory.

## Core Principles
- Store all information in local files.
- Keep entries simple, structured, and inspectable.
- Never require cloud services or external databases.
- Prefer readable plain text and JSON formats.

## Memory Policy
- Every new event must be appended to `memory_log.md` with timestamp.
- Every new event must refresh `memory_map.md` entity aggregates.
- Reminders must be persisted in `reminders.json`.
- Reminder status values: `pending`, `completed`.
- Every `talk` command must also create a conversation file in `conversations/`.
- Every `talk` command must also create a structured context summary in `summaries/`.
- Derived memory views in `memory/` must remain synchronized with the root persisted files.

## Input Conventions
- Log entry format:
  - `YYYY-MM-DD HH:MM - category - description`
- Reminder datetime format:
  - `YYYY-MM-DD HH:MM`

## Assistant Commands
- `talk <text>`: capture a conversation turn, write conversation and context summary files, and update memory.
- `log <text>`: append event to log and update memory map.
- `remind <title> <datetime>`: create reminder with pending status.
- `search <keyword>`: search across log and memory map.
- `today`: list today's log records.
- `context`: show the reusable working context.

## Reliability Rules
- Create missing project files automatically when needed.
- Never delete existing user memory without explicit command.
- Fail with clear messages for invalid datetime input.
