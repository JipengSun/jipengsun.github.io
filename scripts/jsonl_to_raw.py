#!/usr/bin/env python3
"""Write knowledge/raw/{id}.txt from JSON lines of MCP notion-fetch objects (url + text)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "knowledge" / "raw"


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    raw_in = sys.stdin.read()
    for line in raw_in.splitlines():
        line = line.strip()
        if not line:
            continue
        d = json.loads(line)
        url = d.get("url") or ""
        pid = url.rsplit("/", 1)[-1]
        if len(pid) != 32:
            continue
        text = d.get("text") or ""
        out = RAW / f"{pid}.txt"
        if out.exists() and out.stat().st_size > 100:
            continue
        out.write_text(text, encoding="utf-8")
        print(pid)


if __name__ == "__main__":
    main()
