from __future__ import annotations

from datetime import datetime
from pathlib import Path

from utils import (
    CONVERSATIONS_DIR,
    SUMMARIES_DIR,
    extract_entities,
    pending_items_lines,
    timestamp_slug,
    update_working_context,
    write_log,
)


DEFAULT_ASSISTANT_RESPONSE = "Context captured and memory updated."


def _conversation_body(
    when: datetime,
    user_input: str,
    assistant_response: str,
) -> str:
    return "\n".join(
        [
            f"timestamp: {when.strftime('%Y-%m-%d %H:%M')}",
            f"user input: {user_input}",
            f"assistant response: {assistant_response}",
        ]
    ).rstrip() + "\n"


def _summary_body(when: datetime, user_input: str) -> str:
    entities = extract_entities(user_input)
    facts = [f"- {user_input}"]
    entity_lines = [f"- {entity}" for entity in entities] or ["- None"]
    pending_lines = pending_items_lines()
    decisions = ["- None"]
    summary = f"Conversation captured about: {user_input}"

    return "\n".join(
        [
            f"Date: {when.strftime('%Y-%m-%d')}",
            "Facts",
            *facts,
            "Entities",
            *entity_lines,
            "Pending items",
            *pending_lines,
            "Decisions",
            *decisions,
            "Summary",
            summary,
            "",
        ]
    )


def process_conversation(
    message: str,
    assistant_response: str | None = None,
    when: datetime | None = None,
) -> dict:
    when = when or datetime.now()
    assistant_response = (assistant_response or DEFAULT_ASSISTANT_RESPONSE).strip()
    cleaned_message = " ".join(message.strip().split())
    slug = timestamp_slug(when)

    conversation_path = CONVERSATIONS_DIR / f"{slug}.md"
    summary_path = SUMMARIES_DIR / f"{slug}_context.md"

    # The context is refreshed after all related artifacts are written.
    write_log(cleaned_message, when=when, refresh_context=False)
    conversation_path.write_text(
        _conversation_body(when, cleaned_message, assistant_response),
        encoding="utf-8",
    )
    summary_path.write_text(
        _summary_body(when, cleaned_message),
        encoding="utf-8",
    )
    update_working_context()

    return {
        "conversation_path": conversation_path,
        "summary_path": summary_path,
        "assistant_response": assistant_response,
    }
