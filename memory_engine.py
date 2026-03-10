from __future__ import annotations

from utils import (
    ACTIVE_CONTEXT_FILE,
    MEMORY_DIR,
    MEMORY_LOG_MIRROR_FILE,
    MEMORY_MAP_MIRROR_FILE,
    PENDING_ITEMS_FILE,
    sync_memory_views,
    update_working_context,
)


def refresh_memory_artifacts() -> None:
    update_working_context()
    sync_memory_views()


__all__ = [
    "ACTIVE_CONTEXT_FILE",
    "MEMORY_DIR",
    "MEMORY_LOG_MIRROR_FILE",
    "MEMORY_MAP_MIRROR_FILE",
    "PENDING_ITEMS_FILE",
    "refresh_memory_artifacts",
]
