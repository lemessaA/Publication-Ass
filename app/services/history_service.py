from __future__ import annotations

import json
from pathlib import Path
from typing import List

from app.api.models import HistoryItem
from app.config import get_settings


def _get_history_dir() -> Path:
    settings = get_settings()
    base = Path(settings.history_dir)
    base.mkdir(parents=True, exist_ok=True)
    return base


def persist_history(item: HistoryItem) -> None:
    settings = get_settings()
    if settings.history_backend != "file":
        return
    directory = _get_history_dir()
    path = directory / f"{item.id}.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(item.model_dump(mode="json"), f, indent=2)


def load_history_items() -> List[HistoryItem]:
    settings = get_settings()
    if settings.history_backend != "file":
        return []
    directory = _get_history_dir()
    items: List[HistoryItem] = []
    for path in directory.glob("*.json"):
        try:
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            items.append(HistoryItem.model_validate(data))
        except Exception:
            continue
    # Most recent first
    items.sort(key=lambda x: x.created_at, reverse=True)
    return items


def load_history_item(item_id: str) -> HistoryItem | None:
    settings = get_settings()
    if settings.history_backend != "file":
        return None
    path = _get_history_dir() / f"{item_id}.json"
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return HistoryItem.model_validate(data)

