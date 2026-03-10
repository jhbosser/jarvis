from __future__ import annotations

import argparse
from datetime import datetime

from dateutil import parser as dt_parser
from rich.console import Console
from rich.table import Table

from context_engine import process_conversation
from utils import (
    ensure_files,
    next_reminder_id,
    read_working_context,
    read_reminders,
    save_reminders,
    search_logs,
    today_logs,
    write_log,
)


console = Console()


def parse_datetime(value: str) -> datetime:
    try:
        parsed = dt_parser.parse(value)
    except (ValueError, TypeError) as exc:
        raise argparse.ArgumentTypeError(
            "Invalid datetime. Use format YYYY-MM-DD HH:MM."
        ) from exc
    return parsed.replace(second=0, microsecond=0)


def cmd_log(text: str) -> None:
    entry = write_log(text)
    console.print("[green]Saved log:[/green]")
    console.print(entry)


def cmd_talk(text: str) -> None:
    result = process_conversation(text)
    console.print("[green]Conversation captured.[/green]")
    console.print(result["assistant_response"])
    console.print(str(result["conversation_path"]))
    console.print(str(result["summary_path"]))


def cmd_remind(title: str, date_text: str) -> None:
    reminder_dt = parse_datetime(date_text)
    reminders = read_reminders()
    reminder = {
        "id": next_reminder_id(reminders),
        "title": title.strip(),
        "datetime": reminder_dt.strftime("%Y-%m-%d %H:%M"),
        "status": "pending",
    }
    reminders.append(reminder)
    save_reminders(reminders)
    console.print("[green]Reminder created:[/green]")
    console.print(
        f"#{reminder['id']} | {reminder['title']} | {reminder['datetime']} | pending"
    )


def cmd_search(keyword: str) -> None:
    result = search_logs(keyword)
    logs = result["logs"]
    memory_map = result["map"]

    if not logs and not memory_map:
        console.print("[yellow]No matches found.[/yellow]")
        return

    if logs:
        table = Table(title="Log Matches")
        table.add_column("#", justify="right", style="cyan", no_wrap=True)
        table.add_column("Entry", style="white")
        for index, line in enumerate(logs, start=1):
            table.add_row(str(index), line)
        console.print(table)

    if memory_map:
        console.print("\n[bold]Memory Map Matches[/bold]")
        for block in memory_map:
            console.print(block)
            console.print("")


def cmd_today() -> None:
    lines = today_logs()
    if not lines:
        console.print("[yellow]No records for today.[/yellow]")
        return

    table = Table(title=f"Records for {datetime.now().strftime('%Y-%m-%d')}")
    table.add_column("#", justify="right", style="cyan", no_wrap=True)
    table.add_column("Entry", style="white")
    for index, line in enumerate(lines, start=1):
        table.add_row(str(index), line)
    console.print(table)


def cmd_context() -> None:
    console.print(read_working_context())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Jarvis local assistant CLI",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    parser_log = subparsers.add_parser("log", help="Add a log record.")
    parser_log.add_argument("text", help="Text to record.")

    parser_talk = subparsers.add_parser("talk", help="Capture a conversation turn.")
    parser_talk.add_argument("text", help="User message to capture.")

    parser_remind = subparsers.add_parser("remind", help="Create a reminder.")
    parser_remind.add_argument("title", help="Reminder title.")
    parser_remind.add_argument("datetime", help='Datetime, example: "2026-04-10 09:00"')

    parser_search = subparsers.add_parser(
        "search", help="Search in memory log and memory map."
    )
    parser_search.add_argument("keyword", help="Keyword to search.")

    subparsers.add_parser("today", help="Show today's log records.")
    subparsers.add_parser("context", help="Show the persisted working context.")
    return parser


def main() -> None:
    ensure_files()
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "log":
        cmd_log(args.text)
    elif args.command == "talk":
        cmd_talk(args.text)
    elif args.command == "remind":
        cmd_remind(args.title, args.datetime)
    elif args.command == "search":
        cmd_search(args.keyword)
    elif args.command == "today":
        cmd_today()
    elif args.command == "context":
        cmd_context()


if __name__ == "__main__":
    main()
