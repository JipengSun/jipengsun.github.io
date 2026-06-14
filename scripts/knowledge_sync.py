#!/usr/bin/env python3
"""Incremental Notion knowledge sync.

Compare Notion fetch timestamps ("as of …" in notion-fetch text) with local exports,
apply only create/update exports from knowledge/raw/_in, then rebuild HTML + index.

Workflow:
  1. Fetch changed pages with Notion MCP notion-fetch
  2. Save JSON:  python3 scripts/save_notion_fetch_json.py < fetch.json
  3. Plan:       python3 scripts/knowledge_sync.py plan
  4. Apply:      python3 scripts/knowledge_sync.py apply [--force]

Commands:
  plan    Show create / update / unchanged / missing / removed
  apply   Write changed raw/*.txt, rebuild articles + knowledge-share index
  status  Compact summary from sync-state.json
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from notion_md_to_html import NOTION_TO_SLUG, build_full_page, extract_from_mcp_view, notion_body_to_html  # noqa: E402
from notion_images import mirror_images_in_markdown  # noqa: E402
from notion_sync import (  # noqa: E402
    IN_DIR,
    RAW,
    ARTICLES,
    load_incoming_fetch,
    load_state,
    parse_notion_fetched_at,
    plan_sync,
    save_state,
    set_page_record,
)

MCP = ROOT / "scripts" / "mcp_notion_to_raw.py"
BUILD_INDEX = ROOT / "scripts" / "build_knowledge_index.py"


def write_raw_from_fetch(data: dict) -> tuple[str, str]:
    text = data.get("text") or ""
    url = data.get("url") or ""
    page_id = url.rsplit("/", 1)[-1].lower()
    if len(page_id) != 32:
        raise ValueError(f"bad page id in url: {url!r}")
    (RAW / f"{page_id}.txt").write_text(text, encoding="utf-8")
    return page_id, text


def build_article(page_id: str, slug: str, *, force_images: bool = False) -> None:
    raw = (RAW / f"{page_id}.txt").read_text(encoding="utf-8")
    title, body = extract_from_mcp_view(raw)
    body, _ = mirror_images_in_markdown(body, force=force_images)
    inner = notion_body_to_html(body)
    patched = "\t\t\t\t" + inner.replace("\n", "\n\t\t\t\t")
    html_out = build_full_page(title, patched, slug)
    ARTICLES.mkdir(parents=True, exist_ok=True)
    (ARTICLES / f"{slug}.html").write_text(html_out, encoding="utf-8")


def collect_incoming_exports(force_all: bool = False) -> list[tuple[str, dict]]:
    seen: set[str] = set()
    exports: list[tuple[str, dict]] = []

    def consider(data: dict) -> None:
        url = data.get("url") or ""
        page_id = url.rsplit("/", 1)[-1].lower()
        if len(page_id) != 32 or page_id in seen:
            return
        seen.add(page_id)
        exports.append((page_id, data))

    if IN_DIR.is_dir():
        for pattern in ("*.json", "*_fetch.json"):
            for path in sorted(IN_DIR.glob(pattern)):
                consider(json.loads(path.read_text(encoding="utf-8")))
        sources = IN_DIR / "sources"
        if sources.is_dir():
            for path in sorted(sources.glob("*.jsonline")):
                for line in path.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line:
                        consider(json.loads(line))
    return exports


def apply_sync(force: bool = False, rebuild_index: bool = True) -> int:
    state = load_state()
    changed_slugs: list[str] = []
    created = updated = skipped = 0

    for page_id, data in collect_incoming_exports():
        slug = NOTION_TO_SLUG.get(page_id)
        if not slug:
            print(f"skip unmapped {page_id}", file=sys.stderr)
            continue

        text = data.get("text") or ""
        incoming_at = parse_notion_fetched_at(text)
        if incoming_at is None:
            print(f"skip {page_id}: no 'as of' timestamp in fetch text", file=sys.stderr)
            continue

        from notion_sync import read_local_fetched_at

        local_at = read_local_fetched_at(page_id)
        if not force and local_at is not None and incoming_at <= local_at:
            skipped += 1
            continue

        page_id, text = write_raw_from_fetch(data)
        title, _ = extract_from_mcp_view(text)
        build_article(page_id, slug, force_images=True)
        set_page_record(state, page_id, slug=slug, title=title, notion_fetched_at=incoming_at)

        if local_at is None:
            created += 1
            print(f"create {slug} ({page_id})")
        else:
            updated += 1
            print(f"update {slug} ({page_id})")
        changed_slugs.append(slug)

    save_state(state)

    if changed_slugs and rebuild_index:
        subprocess.run([sys.executable, str(BUILD_INDEX)], check=True)

    print(f"done: created={created} updated={updated} skipped={skipped}")
    return 0


def cmd_plan(_: argparse.Namespace) -> int:
    items = plan_sync(NOTION_TO_SLUG)
    groups: dict[str, list] = {}
    for item in items:
        groups.setdefault(item.status, []).append(item)

    for status in ("create", "update", "missing_export", "unmapped", "removed", "orphan_article", "unchanged"):
        bucket = groups.get(status, [])
        if not bucket:
            continue
        print(f"\n[{status}] ({len(bucket)})")
        for item in bucket:
            slug = item.slug or "?"
            extra = f" — {item.detail}" if item.detail else ""
            if item.incoming_at:
                extra = f" — incoming {item.incoming_at.isoformat()}{extra}"
            elif item.local_at:
                extra = f" — local {item.local_at.isoformat()}{extra}"
            print(f"  {slug:32} {item.page_id or '-'}{extra}")
    return 0


def cmd_status(_: argparse.Namespace) -> int:
    state = load_state()
    pages = state.get("pages", {})
    print(f"sync-state: {len(pages)} pages (updated {state.get('updated_at', 'never')})")
    for page_id, rec in sorted(pages.items(), key=lambda kv: kv[1].get("slug", "")):
        print(
            f"  {rec.get('slug', '?'):32} notion={rec.get('notion_fetched_at', '?')} "
            f"synced={rec.get('synced_at', '?')}"
        )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("plan", help="Show what needs fetching or applying")
    p_apply = sub.add_parser("apply", help="Apply newer _in exports and rebuild")
    p_apply.add_argument("--force", action="store_true", help="Rebuild even if timestamps match")
    p_apply.add_argument("--no-index", action="store_true", help="Skip knowledge-share index rebuild")
    sub.add_parser("status", help="Show sync-state.json summary")

    args = parser.parse_args()
    if args.cmd == "plan":
        return cmd_plan(args)
    if args.cmd == "status":
        return cmd_status(args)
    if args.cmd == "apply":
        return apply_sync(force=args.force, rebuild_index=not args.no_index)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
