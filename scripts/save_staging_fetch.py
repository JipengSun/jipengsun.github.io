#!/usr/bin/env python3
"""Write notion-fetch JSON objects from stdin (one JSON object) to knowledge/raw/_in/staging/."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAGING = ROOT / "knowledge" / "raw" / "_in" / "staging"


def save(data: dict) -> str:
    STAGING.mkdir(parents=True, exist_ok=True)
    url = data.get("url") or ""
    pid = url.rsplit("/", 1)[-1].lower()
    if len(pid) != 32:
        raise SystemExit(f"bad url: {url!r}")
    out = STAGING / f"{pid}.json"
    out.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    return pid


def main() -> None:
    data = json.load(sys.stdin)
    print(save(data))


if __name__ == "__main__":
    main()
