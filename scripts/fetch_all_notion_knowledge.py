#!/usr/bin/env python3
"""Fetch all knowledge pages from Notion MCP and rebuild the site.

Requires Notion MCP to be available to the caller. This script is a helper
that writes raw .txt from existing _in/*.json and rebuilds pages.

For a full refresh from live Notion:
  1. Fetch changed pages with notion-fetch MCP (only those listed by `plan`)
  2. Save: python3 scripts/save_notion_fetch_json.py < fetch.json
  3. Run: python3 scripts/knowledge_sync.py apply

See also: python3 scripts/knowledge_sync.py plan
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from notion_md_to_html import NOTION_TO_SLUG  # noqa: E402

SYNC = ROOT / "scripts" / "knowledge_sync.py"


def main() -> None:
    ids = sorted(NOTION_TO_SLUG.keys())
    in_dir = ROOT / "knowledge" / "raw" / "_in"
    missing = [pid for pid in ids if not (in_dir / f"{pid}.json").is_file()]
    print(f"mapped pages: {len(ids)}")
    print(f"missing json exports: {len(missing)}")
    if missing:
        print("fetch these via notion-fetch MCP, save with scripts/save_notion_fetch_json.py")
        for pid in missing:
            print(f"  {pid} -> {NOTION_TO_SLUG[pid]}")
    subprocess.run([sys.executable, str(SYNC), "plan"], check=True)
    subprocess.run([sys.executable, str(SYNC), "apply"], check=True)


if __name__ == "__main__":
    main()
