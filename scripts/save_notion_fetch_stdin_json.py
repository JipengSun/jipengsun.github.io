#!/usr/bin/env python3
"""Read one JSON object (notion-fetch) from stdin; write compact JSON to knowledge/raw/_in/{id}.json."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IN_DIR = ROOT / "knowledge" / "raw" / "_in"


def main() -> None:
    IN_DIR.mkdir(parents=True, exist_ok=True)
    data = json.load(sys.stdin)
    url = data.get("url") or ""
    pid = url.rsplit("/", 1)[-1]
    if len(pid) != 32:
        sys.exit(f"bad url: {url!r}")
    # Compact UTF-8; preserves exact text field string on round-trip.
    out = IN_DIR / f"{pid}.json"
    out.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(pid)


if __name__ == "__main__":
    main()
