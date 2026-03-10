from __future__ import annotations

import time
from datetime import datetime

from dateutil import parser as dt_parser
from plyer import notification
from rich.console import Console

from utils import read_reminders, save_reminders


console = Console()


def reminder_due(reminder: dict, now: datetime) -> bool:
    if reminder.get("status") != "pending":
        return False
    try:
        scheduled = dt_parser.parse(str(reminder.get("datetime", "")))
    except (ValueError, TypeError):
        return False
    return scheduled <= now


def trigger_notification(reminder: dict) -> None:
    title = str(reminder.get("title", "Reminder")).strip() or "Reminder"
    when = str(reminder.get("datetime", "")).strip()
    notification.notify(
        title=f"Jarvis Reminder: {title}",
        message=f"Scheduled for {when}",
        app_name="Jarvis",
        timeout=10,
    )


def run_service() -> None:
    console.print("[bold green]Jarvis reminder service started.[/bold green]")
    while True:
        now = datetime.now()
        reminders = read_reminders()
        changed = False

        for reminder in reminders:
            if reminder_due(reminder, now):
                trigger_notification(reminder)
                reminder["status"] = "completed"
                reminder["completed_at"] = now.strftime("%Y-%m-%d %H:%M")
                changed = True
                console.print(
                    f"[cyan]Completed reminder #{reminder.get('id')}:[/cyan] "
                    f"{reminder.get('title')}"
                )

        if changed:
            save_reminders(reminders)

        time.sleep(60)


if __name__ == "__main__":
    run_service()

