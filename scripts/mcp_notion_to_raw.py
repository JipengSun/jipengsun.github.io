#!/usr/bin/env python3
"""Read one notion-fetch JSON object from stdin; write knowledge/raw/{id}.txt."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from notion_sync import parse_notion_fetched_at, read_local_fetched_at  # noqa: E402

RAW = ROOT / "knowledge" / "raw"


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    args = [a for a in sys.argv[1:] if a != "--force"]
    force = "--force" in sys.argv[1:]
    if args:
        d = json.loads(Path(args[0]).read_text(encoding="utf-8"))
    else:
        d = json.load(sys.stdin)
    url = d.get("url") or ""
    pid = url.rsplit("/", 1)[-1]
    if len(pid) != 32:
        sys.exit("missing 32-char page id in url")
    text = d.get("text") or ""
    out = RAW / f"{pid}.txt"
    incoming_at = parse_notion_fetched_at(text)
    local_at = read_local_fetched_at(pid)
    if (
        not force
        and out.exists()
        and out.stat().st_size > 100
        and incoming_at is not None
        and local_at is not None
        and incoming_at <= local_at
    ):
        print(f"skip {pid} (local {local_at.isoformat()} >= incoming {incoming_at.isoformat()})")
        return
    out.write_text(text, encoding="utf-8")
    print(pid)


if __name__ == "__main__":
    main()

