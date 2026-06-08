#!/usr/bin/env python3
"""Shared helpers for Notion ↔ knowledge site sync (timestamps, state, discovery)."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "knowledge" / "raw"
IN_DIR = RAW / "_in"
ARTICLES = ROOT / "knowledge" / "articles"
STATE_PATH = RAW / "sync-state.json"

FETCH_TIME_RE = re.compile(
    r"as of (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{3})?Z)",
    re.IGNORECASE,
)
PAGE_ID_RE = re.compile(r"notion\.so/([a-f0-9]{32})", re.IGNORECASE)
MENTION_PAGE_RE = re.compile(
    r'<mention-page url="https://(?:www\.notion\.so/|app\.notion\.com/p/)([a-f0-9]{32})"\s*/>',
)


def parse_notion_fetched_at(text: str) -> datetime | None:
    m = FETCH_TIME_RE.search(text)
    if not m:
        return None
    raw = m.group(1)
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


def parse_page_id_from_fetch(text: str) -> str | None:
    m = PAGE_ID_RE.search(text)
    return m.group(1).lower() if m else None


def load_state() -> dict[str, Any]:
    if not STATE_PATH.is_file():
        return {"pages": {}, "updated_at": None}
    return json.loads(STATE_PATH.read_text(encoding="utf-8"))


def save_state(state: dict[str, Any]) -> None:
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def page_record(state: dict[str, Any], page_id: str) -> dict[str, Any] | None:
    return state.get("pages", {}).get(page_id)


def set_page_record(
    state: dict[str, Any],
    page_id: str,
    *,
    slug: str,
    title: str,
    notion_fetched_at: datetime,
) -> None:
    state.setdefault("pages", {})[page_id] = {
        "slug": slug,
        "title": title,
        "notion_fetched_at": notion_fetched_at.isoformat(),
        "synced_at": datetime.now(timezone.utc).isoformat(),
    }


def read_local_fetched_at(page_id: str) -> datetime | None:
    path = RAW / f"{page_id}.txt"
    if not path.is_file():
        return None
    return parse_notion_fetched_at(path.read_text(encoding="utf-8"))


def read_incoming_fetched_at(page_id: str) -> datetime | None:
    for name in (f"{page_id}.json", f"{page_id}_fetch.json"):
        path = IN_DIR / name
        if not path.is_file():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        text = data.get("text") or ""
        return parse_notion_fetched_at(text)
    return None


def load_incoming_fetch(page_id: str) -> dict[str, Any] | None:
    for name in (f"{page_id}.json", f"{page_id}_fetch.json"):
        path = IN_DIR / name
        if path.is_file():
            return json.loads(path.read_text(encoding="utf-8"))
    return None


def discover_mentioned_page_ids() -> set[str]:
    found: set[str] = set()
    for path in RAW.glob("*.txt"):
        text = path.read_text(encoding="utf-8")
        found.update(MENTION_PAGE_RE.findall(text))
        found.add(path.stem.lower())
    return {pid.lower() for pid in found}


@dataclass
class SyncPlanItem:
    page_id: str
    slug: str | None
    status: str  # unchanged | update | create | missing_export | unmapped | removed
    local_at: datetime | None = None
    incoming_at: datetime | None = None
    detail: str = ""


def compare_page(
    page_id: str,
    slug: str | None,
    *,
    local_at: datetime | None,
    incoming_at: datetime | None,
) -> SyncPlanItem:
    if slug is None:
        return SyncPlanItem(page_id, None, "unmapped", local_at, incoming_at, "add to NOTION_TO_SLUG")
    if incoming_at is None:
        if local_at is None:
            return SyncPlanItem(page_id, slug, "missing_export", None, None, "fetch via notion-fetch MCP")
        return SyncPlanItem(page_id, slug, "unchanged", local_at, None, "local copy only")
    if local_at is None:
        return SyncPlanItem(page_id, slug, "create", None, incoming_at, "new local export")
    if incoming_at > local_at:
        return SyncPlanItem(
            page_id,
            slug,
            "update",
            local_at,
            incoming_at,
            f"Notion newer ({incoming_at.isoformat()} > {local_at.isoformat()})",
        )
    if incoming_at < local_at:
        return SyncPlanItem(
            page_id,
            slug,
            "unchanged",
            local_at,
            incoming_at,
            "local is newer than _in export",
        )
    return SyncPlanItem(page_id, slug, "unchanged", local_at, incoming_at, "timestamps match")


def plan_sync(notion_to_slug: dict[str, str]) -> list[SyncPlanItem]:
    items: list[SyncPlanItem] = []
    active_ids = set(notion_to_slug.keys())
    state = load_state()

    for page_id, slug in sorted(notion_to_slug.items()):
        local_at = read_local_fetched_at(page_id)
        incoming_at = read_incoming_fetched_at(page_id)
        items.append(compare_page(page_id, slug, local_at=local_at, incoming_at=incoming_at))

    # Pages mentioned in raw exports but not mapped yet.
    for page_id in sorted(discover_mentioned_page_ids() - active_ids):
        incoming_at = read_incoming_fetched_at(page_id)
        local_at = read_local_fetched_at(page_id)
        items.append(compare_page(page_id, None, local_at=local_at, incoming_at=incoming_at))

    # Removed from mapping but still on disk.
    known_slugs = set(notion_to_slug.values())
    for page_id, rec in sorted(state.get("pages", {}).items()):
        if page_id in active_ids:
            continue
        slug = rec.get("slug", page_id)
        html_path = ARTICLES / f"{slug}.html"
        detail = "removed from NOTION_TO_SLUG"
        if html_path.is_file():
            detail += f"; article still at {html_path.relative_to(ROOT)}"
        items.append(SyncPlanItem(page_id, slug, "removed", detail=detail))

    for slug in sorted(p for p in ARTICLES.glob("*.html") if p.stem not in known_slugs):
        items.append(
            SyncPlanItem(
                "",
                slug.stem,
                "orphan_article",
                detail=f"html without mapping: {slug.relative_to(ROOT)}",
            )
        )

    return items
