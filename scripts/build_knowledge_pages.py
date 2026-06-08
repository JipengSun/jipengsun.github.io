#!/usr/bin/env python3
"""Build knowledge/articles/*.html from knowledge/raw/{notion_id}.txt.

Each file should store the full string returned by Notion MCP notion-fetch (with <page>…</page>).
After re-fetching from Notion, prefer: python3 scripts/knowledge_sync.py apply

Or rebuild all HTML from existing raw files: python3 scripts/build_knowledge_pages.py

Slug mapping: scripts/notion_md_to_html.py NOTION_TO_SLUG (kept in sync with knowledge-share.html).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from notion_md_to_html import (  # noqa: E402
    NOTION_TO_SLUG,
    build_full_page,
    extract_from_mcp_view,
    notion_body_to_html,
)
from notion_sync import load_state, parse_notion_fetched_at, save_state, set_page_record  # noqa: E402


def main() -> None:
    raw_dir = ROOT / "knowledge" / "raw"
    out_dir = ROOT / "knowledge" / "articles"
    if not raw_dir.is_dir():
        print("Missing knowledge/raw — add MCP export .txt files named {notion_id}.txt", file=sys.stderr)
        sys.exit(1)
    out_dir.mkdir(parents=True, exist_ok=True)
    state = load_state()
    for path in sorted(raw_dir.glob("*.txt")):
        pid = path.stem.lower()
        slug = NOTION_TO_SLUG.get(pid)
        if not slug:
            print(f"skip unknown id {pid}", file=sys.stderr)
            continue
        raw = path.read_text(encoding="utf-8")
        title, body = extract_from_mcp_view(raw)
        inner = notion_body_to_html(body)
        patched = "\t\t\t\t" + inner.replace("\n", "\n\t\t\t\t")
        html_out = build_full_page(title, patched, slug)
        (out_dir / f"{slug}.html").write_text(html_out, encoding="utf-8")
        fetched_at = parse_notion_fetched_at(raw)
        if fetched_at is not None:
            set_page_record(state, pid, slug=slug, title=title, notion_fetched_at=fetched_at)
        print(slug)
    save_state(state)


if __name__ == "__main__":
    main()
