from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any

from dateutil import parser as dt_parser
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from context_engine import process_conversation
from memory_engine import refresh_memory_artifacts
from utils import (
    MEMORY_LOG_FILE,
    ensure_files,
    next_reminder_id,
    read_reminders,
    read_working_context,
    save_reminders,
    search_logs,
    today_logs,
    write_log,
)


BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"


def cors_origins_from_env() -> list[str]:
    raw = os.getenv("JARVIS_CORS_ORIGINS", "*").strip()
    if raw == "*":
        return ["*"]
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


class LogCreateRequest(BaseModel):
    text: str = Field(..., min_length=1)


class TalkCreateRequest(BaseModel):
    text: str = Field(..., min_length=1)
    assistant_response: str | None = None


class ReminderCreateRequest(BaseModel):
    title: str = Field(..., min_length=1)
    datetime: str = Field(..., min_length=1)


app = FastAPI(
    title="Jarvis Web API",
    version="0.1.0",
    description="HTTP layer for the local-first Jarvis assistant.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins_from_env(),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


def parse_datetime_input(value: str) -> datetime:
    try:
        parsed = dt_parser.parse(value)
    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=400,
            detail="Invalid datetime. Use format YYYY-MM-DD HH:MM.",
        ) from exc
    return parsed.replace(second=0, microsecond=0)


def read_recent_logs(limit: int = 10) -> list[str]:
    ensure_files()
    lines = [
        line.strip()
        for line in MEMORY_LOG_FILE.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return list(reversed(lines[-limit:]))


def pending_reminders() -> list[dict[str, Any]]:
    return [
        reminder for reminder in read_reminders() if reminder.get("status") == "pending"
    ]


@app.on_event("startup")
def startup() -> None:
    ensure_files()
    refresh_memory_artifacts()


@app.get("/", include_in_schema=False)
def web_index() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/overview")
def overview() -> dict[str, Any]:
    return {
        "today_logs": today_logs(),
        "recent_logs": read_recent_logs(),
        "pending_reminders": pending_reminders(),
        "working_context": read_working_context(),
    }


@app.get("/api/today")
def api_today() -> dict[str, list[str]]:
    return {"entries": today_logs()}


@app.get("/api/context")
def api_context() -> dict[str, str]:
    return {"content": read_working_context()}


@app.get("/api/search")
def api_search(q: str = Query(..., min_length=1)) -> dict[str, Any]:
    result = search_logs(q)
    return {
        "query": q,
        "logs": result["logs"],
        "memory_map": result["map"],
    }


@app.get("/api/reminders")
def api_reminders() -> dict[str, list[dict[str, Any]]]:
    reminders = sorted(read_reminders(), key=lambda item: str(item.get("datetime", "")))
    return {"items": reminders}


@app.post("/api/log")
def api_log(payload: LogCreateRequest) -> dict[str, str]:
    entry = write_log(payload.text)
    return {"entry": entry}


@app.post("/api/talk")
def api_talk(payload: TalkCreateRequest) -> dict[str, str]:
    result = process_conversation(
        payload.text,
        assistant_response=payload.assistant_response,
    )
    return {
        "assistant_response": result["assistant_response"],
        "conversation_path": str(result["conversation_path"]),
        "summary_path": str(result["summary_path"]),
    }


@app.post("/api/reminders")
def api_create_reminder(payload: ReminderCreateRequest) -> dict[str, Any]:
    reminder_dt = parse_datetime_input(payload.datetime)
    reminders = read_reminders()
    reminder = {
        "id": next_reminder_id(reminders),
        "title": payload.title.strip(),
        "datetime": reminder_dt.strftime("%Y-%m-%d %H:%M"),
        "status": "pending",
    }
    reminders.append(reminder)
    save_reminders(reminders)
    return reminder


@app.post("/api/reminders/{reminder_id}/complete")
def api_complete_reminder(reminder_id: str) -> dict[str, Any]:
    reminders = read_reminders()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    for reminder in reminders:
        if str(reminder.get("id")) != reminder_id:
            continue
        reminder["status"] = "completed"
        reminder["completed_at"] = now
        save_reminders(reminders)
        return reminder

    raise HTTPException(status_code=404, detail="Reminder not found.")
