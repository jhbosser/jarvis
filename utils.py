from __future__ import annotations

import json
import os
import re
from collections import deque
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List

try:
    import fcntl
except ImportError:  # pragma: no cover - only relevant outside POSIX environments
    fcntl = None


BASE_DIR = Path(__file__).resolve().parent
MEMORY_DIR = BASE_DIR / "memory"
ARCHIVES_DIR = BASE_DIR / "archives"
CONVERSATIONS_DIR = BASE_DIR / "conversations"
SUMMARIES_DIR = BASE_DIR / "summaries"
MEMORY_LOG_FILE = BASE_DIR / "memory_log.md"
MEMORY_MAP_FILE = BASE_DIR / "memory_map.md"
REMINDERS_FILE = BASE_DIR / "reminders.json"
WORKING_CONTEXT_FILE = BASE_DIR / "WORKING_CONTEXT.md"
LOCK_FILE = BASE_DIR / ".jarvis.lock"
PENDING_ITEMS_FILE = MEMORY_DIR / "pending_items.md"
ACTIVE_CONTEXT_FILE = MEMORY_DIR / "active_context.md"
MEMORY_LOG_MIRROR_FILE = MEMORY_DIR / "memory_log.md"
MEMORY_MAP_MIRROR_FILE = MEMORY_DIR / "memory_map.md"
ACTIVE_LOG_MAX_BYTES = max(
    128 * 1024,
    int(os.getenv("JARVIS_ACTIVE_LOG_MAX_BYTES", str(2 * 1024 * 1024))),
)
ACTIVE_LOG_KEEP_LINES = max(200, int(os.getenv("JARVIS_ACTIVE_LOG_KEEP_LINES", "4000")))
SEARCH_MAX_LOG_MATCHES = max(
    20, int(os.getenv("JARVIS_SEARCH_MAX_LOG_MATCHES", "200"))
)

ENTITY_PATTERN = re.compile(r"\b[A-Z][a-zA-Z0-9_-]{2,}\b")
GENERIC_ENTITY_TOKENS = {
    "supplier",
    "vendor",
    "delivery",
    "client",
    "customer",
    "sale",
    "idea",
    "insight",
    "opportunity",
    "issue",
    "problem",
    "error",
    "bug",
    "note",
}

DEFAULT_WORKING_CONTEXT = """# Working Context

This file stores a reusable context snapshot independent of the current chat.
Sections under `Automatic Context` are maintained by Jarvis. `User Notes` are preserved.

## Automatic Context

### Last updated
- Aguardando atualizacao automatica.

### Current focus
- Ainda sem contexto suficiente.

### Active items
- Nenhum item ativo.

### Recent facts
- Nenhum registro recente.

### Relevant entities
- Nenhuma entidade relevante.

### Open threads
- Nenhum acompanhamento aberto.

## User Notes

### Stable preferences
- Adicione observacoes permanentes que devam sobreviver entre chats.

### Personal context
- Adicione contexto pessoal ou operacional que nao aparece sozinho nos registros.
"""


@dataclass
class EntitySummary:
    entity_type: str = "entity"
    mentions: int = 0
    last_event: str = ""


def ensure_files() -> None:
    for directory in (MEMORY_DIR, ARCHIVES_DIR, CONVERSATIONS_DIR, SUMMARIES_DIR):
        directory.mkdir(parents=True, exist_ok=True)

    for file_path, default_content in (
        (MEMORY_LOG_FILE, ""),
        (MEMORY_MAP_FILE, ""),
        (REMINDERS_FILE, "[]"),
        (WORKING_CONTEXT_FILE, DEFAULT_WORKING_CONTEXT),
        (PENDING_ITEMS_FILE, ""),
        (ACTIVE_CONTEXT_FILE, ""),
        (MEMORY_LOG_MIRROR_FILE, ""),
        (MEMORY_MAP_MIRROR_FILE, ""),
    ):
        if not file_path.exists():
            file_path.write_text(default_content, encoding="utf-8")


@contextmanager
def io_lock():
    ensure_files()
    LOCK_FILE.touch(exist_ok=True)
    with LOCK_FILE.open("r+", encoding="utf-8") as lock_handle:
        if fcntl is not None:
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            if fcntl is not None:
                fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)


def _read_nonempty_lines(file_path: Path) -> List[str]:
    if not file_path.exists():
        return []
    with file_path.open("r", encoding="utf-8") as file:
        return [line.strip() for line in file if line.strip()]


def _archive_log_files(newest_first: bool = False) -> List[Path]:
    files = sorted(ARCHIVES_DIR.glob("memory_log_*.md"))
    return list(reversed(files)) if newest_first else files


def _rotate_memory_log_if_needed() -> None:
    if not MEMORY_LOG_FILE.exists():
        return
    if MEMORY_LOG_FILE.stat().st_size <= ACTIVE_LOG_MAX_BYTES:
        return

    lines = _read_nonempty_lines(MEMORY_LOG_FILE)
    if len(lines) <= ACTIVE_LOG_KEEP_LINES:
        return

    split_index = len(lines) - ACTIVE_LOG_KEEP_LINES
    archive_lines = lines[:split_index]
    active_lines = lines[split_index:]
    archive_name = f"memory_log_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.md"
    archive_path = ARCHIVES_DIR / archive_name

    archive_path.write_text("\n".join(archive_lines).rstrip() + "\n", encoding="utf-8")
    MEMORY_LOG_FILE.write_text("\n".join(active_lines).rstrip() + "\n", encoding="utf-8")


def normalize_log_text(text: str) -> str:
    return " ".join(text.strip().split())


def detect_category(text: str) -> str:
    lowered = text.lower()
    if any(token in lowered for token in ("supplier", "vendor", "delivery")):
        return "supplier"
    if any(token in lowered for token in ("client", "customer", "sale")):
        return "client"
    if any(token in lowered for token in ("idea", "insight", "opportunity")):
        return "idea"
    if any(token in lowered for token in ("issue", "problem", "error", "bug")):
        return "problem"
    return "note"


def extract_entities(text: str) -> List[str]:
    entities: List[str] = []
    seen = set()
    for match in ENTITY_PATTERN.finditer(text):
        token = match.group(0)
        if token.lower() in {"the", "and", "for", "with"}:
            continue
        if token.lower() in GENERIC_ENTITY_TOKENS:
            continue
        if token not in seen:
            seen.add(token)
            entities.append(token)
    return entities


def write_log(
    text: str,
    when: datetime | None = None,
    refresh_context: bool = True,
) -> str:
    ensure_files()
    when = when or datetime.now()
    cleaned = normalize_log_text(text)
    category = detect_category(cleaned)
    line = f"{when.strftime('%Y-%m-%d %H:%M')} - {category} - {cleaned}"

    with io_lock():
        with MEMORY_LOG_FILE.open("a", encoding="utf-8") as file:
            if MEMORY_LOG_FILE.stat().st_size > 0:
                file.write("\n")
            file.write(line)

        _rotate_memory_log_if_needed()
        update_memory_map(line)
        if refresh_context:
            update_working_context()
    return line


def _parse_log_line(line: str) -> str:
    parts = [segment.strip() for segment in line.split(" - ", maxsplit=2)]
    if len(parts) == 3:
        return parts[2]
    return line.strip()


def _load_memory_map() -> Dict[str, EntitySummary]:
    summary: Dict[str, EntitySummary] = {}
    content = MEMORY_MAP_FILE.read_text(encoding="utf-8").strip()
    if not content:
        return summary

    blocks = [block.strip() for block in content.split("\n\n") if block.strip()]
    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines:
            continue
        entity = lines[0]
        entity_type = "entity"
        mentions = 0
        last_event = ""
        for line in lines[1:]:
            if line.startswith("type:"):
                entity_type = line.split(":", maxsplit=1)[1].strip() or "entity"
            elif line.startswith("mentions:"):
                mentions_raw = line.split(":", maxsplit=1)[1].strip()
                if mentions_raw.isdigit():
                    mentions = int(mentions_raw)
            elif line.startswith("last_event:"):
                last_event = line.split(":", maxsplit=1)[1].strip()
        summary[entity] = EntitySummary(
            entity_type=entity_type,
            mentions=mentions,
            last_event=last_event,
        )
    return summary


def _save_memory_map(summary: Dict[str, EntitySummary]) -> None:
    if not summary:
        MEMORY_MAP_FILE.write_text("", encoding="utf-8")
        sync_memory_views()
        return

    ordered_entities = sorted(summary.keys(), key=str.lower)
    blocks = []
    for entity in ordered_entities:
        item = summary[entity]
        block = "\n".join(
            [
                entity,
                f"type: {item.entity_type}",
                f"mentions: {item.mentions}",
                f"last_event: {item.last_event}",
            ]
        )
        blocks.append(block)
    MEMORY_MAP_FILE.write_text("\n\n".join(blocks) + "\n", encoding="utf-8")
    sync_memory_views()


def update_memory_map(log_line: str) -> None:
    ensure_files()
    event_description = _parse_log_line(log_line)
    entities = extract_entities(event_description)
    if not entities:
        return

    summary = _load_memory_map()
    category = detect_category(event_description)
    for entity in entities:
        item = summary.get(entity, EntitySummary(entity_type=category))
        item.mentions += 1
        item.last_event = event_description
        if item.entity_type == "entity":
            item.entity_type = category
        summary[entity] = item
    _save_memory_map(summary)


def read_reminders() -> List[dict]:
    ensure_files()
    try:
        content = REMINDERS_FILE.read_text(encoding="utf-8").strip()
        if not content:
            return []
        data = json.loads(content)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def save_reminders(reminders: List[dict]) -> None:
    ensure_files()
    with io_lock():
        REMINDERS_FILE.write_text(
            json.dumps(reminders, ensure_ascii=True, indent=2),
            encoding="utf-8",
        )
        update_working_context()


def next_reminder_id(reminders: List[dict]) -> str:
    highest = 0
    for reminder in reminders:
        reminder_id = str(reminder.get("id", "")).strip()
        if reminder_id.isdigit():
            highest = max(highest, int(reminder_id))
    return str(highest + 1)


def _replace_section(content: str, heading: str, lines: List[str]) -> str:
    pattern = re.compile(
        rf"(^### {re.escape(heading)}\n)(.*?)(?=^## |^### |\Z)",
        re.MULTILINE | re.DOTALL,
    )
    replacement = "\\1" + "\n".join(lines).rstrip() + "\n\n"
    if pattern.search(content):
        return pattern.sub(replacement, content, count=1)
    return content.rstrip() + f"\n\n### {heading}\n" + "\n".join(lines).rstrip() + "\n"


def _last_updated_lines() -> List[str]:
    return [f"- {datetime.now().strftime('%Y-%m-%d %H:%M')}"]


def _pending_reminders() -> List[dict]:
    pending = [
        reminder for reminder in read_reminders() if reminder.get("status") == "pending"
    ]
    pending.sort(key=lambda item: str(item.get("datetime", "")))
    return pending


def pending_items_lines() -> List[str]:
    pending = _pending_reminders()
    if pending:
        return [
            f"- {item.get('title', '')} | {item.get('datetime', '')}"
            for item in pending
        ]
    return ["- None"]


def _recent_logs(limit: int = 5) -> List[str]:
    if limit <= 0:
        return []
    with MEMORY_LOG_FILE.open("r", encoding="utf-8") as file:
        tail = deque((line.strip() for line in file if line.strip()), maxlen=limit)
    return list(tail)


def _current_focus_lines() -> List[str]:
    pending = _pending_reminders()
    recent_logs = _recent_logs(limit=1)
    if pending:
        next_item = pending[0]
        return [
            f"- Prioridade atual inferida: preparar ou acompanhar `{next_item.get('title', '')}` em {next_item.get('datetime', '')}."
        ]
    if recent_logs:
        return [f"- Foco inferido pelos registros recentes: {_parse_log_line(recent_logs[-1])}"]
    return ["- Ainda sem contexto suficiente."]


def _active_items_lines() -> List[str]:
    pending = _pending_reminders()
    if pending:
        return [
            f"- Lembrete pendente: {item.get('title', '')} em {item.get('datetime', '')}"
            for item in pending
        ]

    recent_logs = _recent_logs(limit=3)
    if recent_logs:
        return [
            f"- Sem lembretes pendentes; ultimo movimento registrado: {_parse_log_line(recent_logs[-1])}"
        ]
    return ["- Nenhum item ativo."]


def _recent_facts_lines() -> List[str]:
    recent_logs = _recent_logs()
    if not recent_logs:
        return ["- Nenhum registro recente."]
    return [f"- {line}" for line in reversed(recent_logs)]


def _relevant_entities_lines(limit: int = 5) -> List[str]:
    ignored_tokens = {"tenho", "amanha", "hoje"}
    summary = _load_memory_map()
    if not summary:
        return ["- Nenhuma entidade relevante."]

    ordered = sorted(
        (
            (entity, item)
            for entity, item in summary.items()
            if entity.strip() and entity.lower() not in ignored_tokens
        ),
        key=lambda pair: (-pair[1].mentions, pair[0].lower()),
    )[:limit]
    if not ordered:
        return ["- Nenhuma entidade relevante."]
    return [
        f"- {entity} | tipo: {item.entity_type} | mencoes: {item.mentions} | ultimo evento: {item.last_event}"
        for entity, item in ordered
    ]


def _open_threads_lines() -> List[str]:
    lines: List[str] = []
    for reminder in _pending_reminders()[:5]:
        lines.append(
            f"- Acompanhamento aberto: confirmar `{reminder.get('title', '')}` ate {reminder.get('datetime', '')}."
        )

    for line in reversed(_recent_logs(limit=3)):
        description = _parse_log_line(line)
        lines.append(f"- Fato recente para manter em contexto: {description}")

    if not lines:
        return ["- Nenhum acompanhamento aberto."]
    return lines[:5]


def active_context_lines() -> List[str]:
    recent_entities = _relevant_entities_lines()
    pending_items = pending_items_lines()
    recent_topics = [
        f"- {_parse_log_line(line)}" for line in reversed(_recent_logs(limit=5))
    ]
    if not recent_topics:
        recent_topics = ["- None"]
    recent_decisions = [
        f"- Reminder scheduled: {item.get('title', '')} at {item.get('datetime', '')}"
        for item in _pending_reminders()[:5]
    ]
    if not recent_decisions:
        recent_decisions = ["- None"]

    return [
        "Recent entities",
        *recent_entities,
        "",
        "Active pending items",
        *pending_items,
        "",
        "Recent topics",
        *recent_topics,
        "",
        "Recent decisions",
        *recent_decisions,
    ]


def sync_memory_views() -> None:
    if not MEMORY_DIR.exists():
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    if not PENDING_ITEMS_FILE.exists():
        PENDING_ITEMS_FILE.write_text("", encoding="utf-8")
    if not ACTIVE_CONTEXT_FILE.exists():
        ACTIVE_CONTEXT_FILE.write_text("", encoding="utf-8")
    if not MEMORY_LOG_MIRROR_FILE.exists():
        MEMORY_LOG_MIRROR_FILE.write_text("", encoding="utf-8")
    if not MEMORY_MAP_MIRROR_FILE.exists():
        MEMORY_MAP_MIRROR_FILE.write_text("", encoding="utf-8")

    MEMORY_LOG_MIRROR_FILE.write_text(
        MEMORY_LOG_FILE.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    MEMORY_MAP_MIRROR_FILE.write_text(
        MEMORY_MAP_FILE.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    PENDING_ITEMS_FILE.write_text(
        "\n".join(pending_items_lines()).rstrip() + "\n",
        encoding="utf-8",
    )
    ACTIVE_CONTEXT_FILE.write_text(
        "\n".join(active_context_lines()).rstrip() + "\n",
        encoding="utf-8",
    )


def update_working_context() -> None:
    ensure_files()
    content = WORKING_CONTEXT_FILE.read_text(encoding="utf-8")
    content = _replace_section(
        content,
        "Last updated",
        _last_updated_lines(),
    )
    content = _replace_section(
        content,
        "Current focus",
        _current_focus_lines(),
    )
    content = _replace_section(
        content,
        "Active items",
        _active_items_lines(),
    )
    content = _replace_section(
        content,
        "Recent facts",
        _recent_facts_lines(),
    )
    content = _replace_section(
        content,
        "Relevant entities",
        _relevant_entities_lines(),
    )
    content = _replace_section(
        content,
        "Open threads",
        _open_threads_lines(),
    )
    WORKING_CONTEXT_FILE.write_text(content.rstrip() + "\n", encoding="utf-8")
    sync_memory_views()


def read_working_context() -> str:
    ensure_files()
    return WORKING_CONTEXT_FILE.read_text(encoding="utf-8").strip()


def search_logs(keyword: str) -> dict:
    ensure_files()
    keyword_lower = keyword.lower().strip()

    log_matches = []
    seen_lines = set()
    log_files = [MEMORY_LOG_FILE, *_archive_log_files(newest_first=True)]
    for file_path in log_files:
        with file_path.open("r", encoding="utf-8") as file:
            for raw_line in file:
                line = raw_line.strip()
                if not line:
                    continue
                if keyword_lower and keyword_lower in line.lower():
                    if line in seen_lines:
                        continue
                    seen_lines.add(line)
                    log_matches.append(line)
                    if len(log_matches) >= SEARCH_MAX_LOG_MATCHES:
                        break
        if len(log_matches) >= SEARCH_MAX_LOG_MATCHES:
            break

    map_matches = []
    blocks = MEMORY_MAP_FILE.read_text(encoding="utf-8").strip().split("\n\n")
    for block in blocks:
        normalized = block.strip()
        if not normalized:
            continue
        if keyword_lower and keyword_lower in normalized.lower():
            map_matches.append(normalized)

    return {"logs": log_matches, "map": map_matches}


def today_logs(today: datetime | None = None) -> List[str]:
    ensure_files()
    today = today or datetime.now()
    prefix = today.strftime("%Y-%m-%d")
    day_token = today.strftime("%Y%m%d")
    lines = []
    seen = set()

    for file_path in [*_archive_log_files(), MEMORY_LOG_FILE]:
        if file_path.parent == ARCHIVES_DIR and day_token not in file_path.name:
            continue
        with file_path.open("r", encoding="utf-8") as file:
            for raw_line in file:
                line = raw_line.strip()
                if not line or not line.startswith(prefix):
                    continue
                if line in seen:
                    continue
                seen.add(line)
                lines.append(line)

    return sorted(lines, key=lambda item: item[:16])


def timestamp_slug(when: datetime | None = None) -> str:
    when = when or datetime.now()
    return when.strftime("%Y-%m-%d_%H%M")
