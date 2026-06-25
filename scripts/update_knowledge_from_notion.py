#!/usr/bin/env python3
"""Update the Knowledge Share site from Notion notion-fetch JSON.

Efficient incremental sync: only rebuilds pages whose Notion snapshot is newer
than the local copy (compares the "as of …" timestamp in fetch text).

Typical workflow (from Cursor with Notion MCP):
  1. notion-fetch changed page(s)
  2. python3 scripts/update_knowledge_from_notion.py sync < page.json
     — or pipe JSONL for multiple pages

Commands:
  sync     Ingest fetch JSON from stdin (one object or JSONL) and apply updates
  ingest   Save fetch JSON to knowledge/raw/_in/ without rebuilding
  apply    Apply pending _in exports (same as knowledge_sync.py apply)
  plan     Show what needs fetching or applying

For a new page, add its Notion page id → slug mapping in
scripts/notion_md_to_html.py NOTION_TO_SLUG and (optionally) TOPIC in
scripts/build_knowledge_index.py before syncing.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from knowledge_sync import (  # noqa: E402
    apply_sync,
    cmd_plan,
    ingest_fetch,
    sync_fetches,
)


def load_fetches_from_stdin() -> list[dict]:
    raw = sys.stdin.read().strip()
    if not raw:
        raise SystemExit("stdin is empty — pipe a notion-fetch JSON object or JSONL")
    try:
        data = json.loads(raw)
        return [data] if isinstance(data, dict) else list(data)
    except json.JSONDecodeError:
        fetches: list[dict] = []
        for line in raw.splitlines():
            line = line.strip()
            if line:
                fetches.append(json.loads(line))
        if not fetches:
            raise SystemExit("no JSON objects found on stdin")
        return fetches


def load_fetches_from_path(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        raise SystemExit(f"empty file: {path}")
    try:
        data = json.loads(text)
        return [data] if isinstance(data, dict) else list(data)
    except json.JSONDecodeError:
        return [json.loads(line) for line in text.splitlines() if line.strip()]


def cmd_sync(args: argparse.Namespace) -> int:
    if args.file:
        fetches = load_fetches_from_path(Path(args.file))
    else:
        fetches = load_fetches_from_stdin()
    sync_fetches(fetches, force=args.force, rebuild_index=not args.no_index)
    return 0


def cmd_ingest(args: argparse.Namespace) -> int:
    fetches = load_fetches_from_path(Path(args.file)) if args.file else load_fetches_from_stdin()
    for data in fetches:
        print(ingest_fetch(data))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_sync = sub.add_parser("sync", help="Ingest + rebuild changed pages from stdin or --file")
    p_sync.add_argument("--file", "-f", help="notion-fetch JSON or JSONL file")
    p_sync.add_argument("--force", action="store_true", help="Rebuild even if timestamps match")
    p_sync.add_argument("--no-index", action="store_true", help="Skip knowledge-share index rebuild")

    p_ingest = sub.add_parser("ingest", help="Save fetch JSON to _in/ only")
    p_ingest.add_argument("--file", "-f", help="notion-fetch JSON or JSONL file")

    p_apply = sub.add_parser("apply", help="Apply all pending _in exports")
    p_apply.add_argument("--force", action="store_true")
    p_apply.add_argument("--no-index", action="store_true")

    sub.add_parser("plan", help="Show create/update/unchanged status")

    args = parser.parse_args()
    if args.cmd == "sync":
        return cmd_sync(args)
    if args.cmd == "ingest":
        return cmd_ingest(args)
    if args.cmd == "apply":
        return apply_sync(force=args.force, rebuild_index=not args.no_index)
    if args.cmd == "plan":
        return cmd_plan(args)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
