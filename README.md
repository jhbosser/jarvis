# Jarvis Local Assistant

Jarvis is a local personal assistant that stores memory as files and runs on Python.

## Features
- Capture conversations (`talk`)
- Log events and notes (`log`)
- Create scheduled reminders (`remind`)
- Search across historical records (`search`)
- List today's records (`today`)
- Run background reminder notifications (`reminder_service.py`)

## Project Files
- `instructions.md`: behavior and operational rules
- `memory_log.md`: chronological memory log
- `memory_map.md`: aggregated entity map
- `memory/`: derived memory views aligned with the context engine spec
- `conversations/`: saved conversation turns
- `summaries/`: structured context summaries per conversation
- `reminders.json`: persisted reminders
- `WORKING_CONTEXT.md`: reusable agent-maintained context snapshot plus preserved user notes
- `jarvis.py`: CLI entrypoint
- `context_engine.py`: conversation capture and summary generation
- `memory_engine.py`: derived memory view refresh helpers
- `reminder_engine.py`: reminder engine compatibility module
- `reminder_service.py`: background notifier
- `utils.py`: helper and persistence functions

## Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage
Register a note:
```bash
python jarvis.py log "Supplier Pradolux delayed delivery"
```

Capture a conversation:
```bash
python jarvis.py talk "Victor foi para Cachoeiro hoje."
```

Create a reminder:
```bash
python jarvis.py remind "Review ads" "2026-04-10 09:00"
```

Search records:
```bash
python jarvis.py search "Pradolux"
```

View today's notes:
```bash
python jarvis.py today
```

Run reminder service:
```bash
python reminder_service.py
```

Run the web interface locally:
```bash
uvicorn app.main:app --reload
```
Then open `http://127.0.0.1:8000`.

## Deploy Teste (Web)
This project now supports a quick public test with:
- backend API on Render
- frontend static UI on Netlify

### 1) Deploy backend on Render
- Connect this repository on Render.
- Use `render.yaml` from the project root.
- Confirm service start command:
  - `python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- After deploy, verify:
  - `https://<your-render-app>/health`

Important:
- Current persistence is file-based (`memory_log.md`, `memory_map.md`, `reminders.json`).
- On hosted environments, local disk may be ephemeral depending on the plan/platform.
- For production durability, migrate storage to a managed database.
- Active log rotation keeps `memory_log.md` compact and archives older slices in `archives/`.

### 2) Deploy frontend on Netlify
- Connect this same repository on Netlify.
- Publish directory is already configured in `netlify.toml` as `frontend`.
- After deploy, open the Netlify URL.
- In the page header, set `URL da API` to your Render backend URL.
- Click `Salvar URL`, then `Testar conexao`.

### 3) CORS setup
- For quick tests, backend default is `JARVIS_CORS_ORIGINS="*"`.
- For stricter setup, configure on Render:
  - `JARVIS_CORS_ORIGINS=https://<your-netlify-site>`

### 4) Performance guardrails
- Optional environment variables:
  - `JARVIS_ACTIVE_LOG_MAX_BYTES` (default `2097152`)
  - `JARVIS_ACTIVE_LOG_KEEP_LINES` (default `4000`)
  - `JARVIS_SEARCH_MAX_LOG_MATCHES` (default `200`)
- Rotation preserves old records in `archives/memory_log_*.md`.
- Search and today views read active + archive slices as needed.

## Status: Netlify vs Supabase
- Netlify path: ready now (frontend static + backend API URL field).
- Supabase path: not yet integrated in the application runtime.
- Current persistence remains file-based by design, even for hosted tests.

## Publish via GitHub
1. Initialize repository locally (if this folder is not a git repo):
   - `git init`
   - `git add .`
   - `git commit -m "Initial Jarvis web-ready baseline"`
2. Create a GitHub repository (empty, without README/license from UI).
3. Add remote and push:
   - `git remote add origin <your-github-repo-url>`
   - `git branch -M main`
   - `git push -u origin main`
4. Connect this GitHub repo on:
   - Render (backend)
   - Netlify (frontend, publish dir `frontend`)

Note:
- `.gitignore` excludes local personal memory artifacts (`memory/`, `conversations/`, `summaries/`, root memory files, `reminders.json`) to avoid data leakage when publishing.

## Project Overview
Jarvis is a local-first Python project for automation of note capture, reminder scheduling, lightweight data processing, and generation of console-oriented outputs from structured local files. The repository is intentionally simple: local persistence, explicit formats, and minimal moving parts.

## Architecture
- CLI layer in `jarvis.py`
- Conversation processing in `context_engine.py`
- Memory artifact synchronization in `memory_engine.py`
- Background reminder polling in `reminder_service.py`
- Persistence and search helpers in `utils.py`
- File-based storage in `memory_log.md`, `memory_map.md`, `reminders.json`, and derived files under `memory/`
- Operational rules in `instructions.md`

## Repository Structure
- `jarvis.py`: main command-line interface
- `context_engine.py`: conversation log and context summary generation
- `memory_engine.py`: synchronization for memory views under `memory/`
- `reminder_engine.py`: reminder service compatibility entrypoint
- `reminder_service.py`: due-reminder watcher and notifier
- `utils.py`: file utilities and business flow helpers
- `instructions.md`: behavior guide
- `memory_log.md`: chronological event storage
- `memory_map.md`: entity summary map
- `memory/active_context.md`: spec-aligned active context snapshot
- `memory/pending_items.md`: open pending items derived from reminders
- `memory/memory_log.md`: mirror of the root log file
- `memory/memory_map.md`: mirror of the root memory map
- `conversations/`: conversation logs in `YYYY-MM-DD_HHMM.md`
- `summaries/`: structured context summaries in `YYYY-MM-DD_HHMM_context.md`
- `reminders.json`: reminder persistence
- `PROJECT_CONTEXT.md`: domain context for AI agents and contributors
- `AGENTS.md`: repository operating rules for AI coding agents
- `CLAUDE.md`: Claude Code specific workflow instructions
- `docs/`: business rules, contracts, layouts, and validation docs
- `examples/`: fictitious sample input and output files

## Installation
The current project already includes `requirements.txt`. Install in a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## How to Run
Common commands:

```bash
python3 jarvis.py log "Victor foi para Cachoeiro hoje."
python3 jarvis.py talk "Victor foi para Cachoeiro hoje."
python3 jarvis.py remind "Corretor" "2026-03-11 08:30"
python3 jarvis.py search "Victor"
python3 jarvis.py today
python3 jarvis.py context
python3 reminder_service.py
```

## Inputs
- Free-text event descriptions passed through the CLI
- Free-text conversation messages passed to `talk`
- Reminder titles and datetimes in `YYYY-MM-DD HH:MM`
- Existing persisted records stored in project root files
- Automatic and user-preserved context maintained in `WORKING_CONTEXT.md`

Input contracts and schema expectations are documented in `docs/data_contracts.md`.

## Outputs
- New entries appended to `memory_log.md`
- Old log slices rotated to `archives/memory_log_*.md` when active file grows beyond threshold
- Updated entity summaries in `memory_map.md`
- Conversation records written to `conversations/`
- Context summaries written to `summaries/`
- Derived memory views refreshed under `memory/`
- Reminder records written to `reminders.json`
- Refreshed cross-chat context written to `WORKING_CONTEXT.md`
- Console tables and status messages
- Desktop notifications for due reminders
- Browser-based dashboard for local and mobile-friendly use via the FastAPI web layer

Output layouts must remain aligned with `docs/report_layouts.md`.

## Troubleshooting
- If a command fails on datetime parsing, use `YYYY-MM-DD HH:MM`.
- If notifications do not appear, verify local OS notification permissions and `plyer` support.
- If persisted files look inconsistent, inspect `memory_log.md`, `memory_map.md`, and `reminders.json` before changing code.
- If a new chat lacks operational context, inspect `WORKING_CONTEXT.md` or run `python3 jarvis.py context`.
- Before implementation changes, read `PROJECT_CONTEXT.md`, `AGENTS.md`, and the files inside `docs/`.

## Web MVP
- The repository now includes a first web layer in `app/` and `frontend/`.
- This first step keeps the existing local files as the source of truth.
- For the current scope, the browser interface is single-prompt: one input field drives log capture, reminder management, search, today's entries, context, and conversation capture.
- Deployment direction and online testing flow are documented in `docs/web_mvp.md`.
