#!/usr/bin/env python3
"""Parse newline-delimited notion-fetch JSON objects; write knowledge/raw/{id}.txt (skip if >100B)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "knowledge" / "raw"


def write_one(d: dict) -> None:
    url = d.get("url") or ""
    pid = url.rsplit("/", 1)[-1]
    if len(pid) != 32:
        raise SystemExit(f"missing 32-char page id in url: {url!r}")
    text = d.get("text") or ""
    out = RAW / f"{pid}.txt"
    if out.exists() and out.stat().st_size > 100:
        print("skip", pid)
        return
    out.write_text(text, encoding="utf-8")
    print("wrote", pid, len(text))


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    if len(sys.argv) > 1:
        for path in sys.argv[1:]:
            data = Path(path).read_text(encoding="utf-8")
            for line in data.splitlines():
                line = line.strip()
                if not line:
                    continue
                write_one(json.loads(line))
    else:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            write_one(json.loads(line))


if __name__ == "__main__":
    main()
